from __future__ import annotations

import json
import math
import random
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import GEMINI_ACCOUNTS_CONFIG_PATH, QWEN_ACCOUNTS_CONFIG_PATH
from core.logging import get_logger
from services.account_state_store import (
    AccountStatePaths,
    load_quota_exhausted_at,
    save_quota_exhausted_at,
)

logger = get_logger(__name__)


class AccountRouterError(RuntimeError):
    """Configuration or state error in account router."""


class AllAccountsExhaustedError(AccountRouterError):
    """Raised when all accounts in rounding mode are marked exhausted."""


@dataclass(slots=True)
class BaseAccount:
    name: str
    credentials_path: str


@dataclass(slots=True)
class GeminiAccount(BaseAccount):
    project_id: str


@dataclass(slots=True)
class ProviderGroup:
    accounts: list[str]
    models: list[str]


@dataclass(slots=True)
class ProviderConfig:
    provider: str
    mode: str
    active_account: str
    all_accounts: list[str]
    accounts: dict[str, BaseAccount]
    rate_limit_threshold: int
    quota_exhausted_threshold: int
    rate_limit_cooldown_seconds: int
    random_order: bool
    rotate_after_n_successes: int
    model_quota_resets: dict[str, str]
    groups: dict[str, ProviderGroup]


@dataclass(slots=True)
class SelectedAccount:
    provider: str
    mode: str
    account: BaseAccount
    pool: list[str]
    model: str | None = None


@dataclass(slots=True)
class _ProviderState:
    next_index: int = 0
    has_selected: bool = False
    consecutive_rate_limit_errors: dict[str, int] = field(default_factory=dict)
    consecutive_quota_exhausted_errors: dict[str, int] = field(default_factory=dict)
    cooldown_until: dict[str, float] = field(default_factory=dict)
    quota_exhausted_until: dict[str, dict[str, float]] = field(default_factory=dict)
    successes_on_account: dict[str, int] = field(default_factory=dict)


class RotationEvent:
    RATE_LIMIT = "rate_limit"
    QUOTA_EXHAUSTED = "quota_exhausted"


class RotationDecision:
    RETRY_SAME = "retry_same"
    SWITCH_ACCOUNT = "switch_account"
    ALL_EXHAUSTED = "all_exhausted"
    ALL_COOLDOWN = "all_cooldown"
    NO_ACTION = "no_action"


@dataclass(slots=True)
class EventResult:
    decision: str
    switched: bool
    all_exhausted: bool
    all_cooldown: bool


class QuotaAccountRouter:
    """Provider-aware account router for quota flows.

    Supports:
    - `single`: only active_account.
    - `rounding`: round-robin over all_accounts and switch after 2
      consecutive quota-limit errors.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state: dict[tuple[str, str], _ProviderState] = {}

    def select_account(
        self,
        provider: str,
        model: str | None = None,
        group_id: str = "g0",
    ) -> SelectedAccount:
        provider = self._normalize_provider_id(provider)
        cfg = self._load_provider_config(provider)
        pool = self._resolve_pool(cfg, group_id)
        if cfg.mode == "single":
            account = self._require_account(cfg, cfg.active_account)
            return SelectedAccount(
                provider=provider,
                mode=cfg.mode,
                account=account,
                pool=[cfg.active_account],
                model=model,
            )

        if not pool:
            raise AccountRouterError(
                f"Provider '{provider}' has mode=rounding but pool is empty"
            )

        with self._lock:
            state = self._state.setdefault((provider, group_id), _ProviderState())
            for account_name in pool:
                self._hydrate_exhausted_state(cfg, state, account_name, model)
            self._cleanup_state_for_model_unlocked(state, cfg, model)

            if self._all_exhausted(state, pool, model):
                # Fail fast and allow future recovery attempts on next requests.
                logger.warning(
                    f"[{provider}] rounding: all accounts exhausted (model={model}|group={group_id})"
                )
                self._reset_exhausted_unlocked(provider, group_id)
                raise AllAccountsExhaustedError("all_accounts_exceed_quota")

            if self._all_cooldown(state, pool):
                wait_seconds = self._cooldown_wait_seconds(state, pool)
                logger.warning(
                    f"[{provider}] rounding: all accounts on cooldown "
                    f"(model={model}|group={group_id}|wait={wait_seconds}s)"
                )
                raise AccountRouterError(
                    f"all accounts on cooldown please wait {wait_seconds}"
                )

            if cfg.random_order:
                if not state.has_selected:
                    chosen = self._choose_random_available(state, pool, model)
                    if chosen is not None:
                        state.next_index = pool.index(chosen)
                    state.has_selected = True
                else:
                    current_name = pool[state.next_index % len(pool)]
                    if self._is_exhausted(state, current_name, model) or self._is_on_cooldown(
                        state, current_name
                    ):
                        chosen = self._choose_random_available(state, pool, model)
                        if chosen is not None:
                            state.next_index = pool.index(chosen)

            start = state.next_index % len(pool)
            for offset in range(len(pool)):
                idx = (start + offset) % len(pool)
                candidate = pool[idx]
                if self._is_exhausted(state, candidate, model):
                    continue
                if self._is_on_cooldown(state, candidate):
                    continue
                state.next_index = idx
                account = self._require_account(cfg, candidate)
                reason = "rotation" if offset > 0 else "initial"
                logger.info(
                    f"[{provider}] rounding: selected account={candidate} "
                    f"(reason={reason}|attempt={offset + 1}|model={model}|group={group_id})"
                )
                return SelectedAccount(
                    provider=provider,
                    mode=cfg.mode,
                    account=account,
                    pool=list(pool),
                    model=model,
                )

        if self._all_exhausted(state, pool, model):
            raise AllAccountsExhaustedError("all_accounts_exceed_quota")

        wait_seconds = self._cooldown_wait_seconds(state, pool)
        raise AccountRouterError(
            f"all accounts on cooldown please wait {wait_seconds}"
        )

    def register_success(
        self,
        provider: str,
        account_name: str,
        group_id: str = "g0",
    ) -> None:
        provider = self._normalize_provider_id(provider)
        cfg = self._load_provider_config(provider)
        pool = self._resolve_pool(cfg, group_id)
        with self._lock:
            state = self._state.setdefault((provider, group_id), _ProviderState())
            if account_name in pool:
                self._hydrate_exhausted_state(cfg, state, account_name, None)
            state.consecutive_rate_limit_errors[account_name] = 0
            state.consecutive_quota_exhausted_errors[account_name] = 0
            state.cooldown_until.pop(account_name, None)

            if cfg.mode != "rounding":
                return
            if cfg.rotate_after_n_successes <= 0:
                return

            current = state.successes_on_account.get(account_name, 0) + 1
            state.successes_on_account[account_name] = current
            if current < cfg.rotate_after_n_successes:
                return

            state.successes_on_account[account_name] = 0
            if self._set_next_available_unlocked(
                state,
                pool,
                account_name,
                model=None,
                random_order=cfg.random_order,
            ):
                next_account = pool[state.next_index]
                logger.info(
                    f"[{provider}] rounding: switching {account_name} -> {next_account} "
                    f"(trigger=BY_N|group={group_id}|threshold={cfg.rotate_after_n_successes})"
                )

    def register_quota_limit(
        self,
        provider: str,
        account_name: str,
        mode: str,
        pool: list[str],
        group_id: str = "g0",
    ) -> bool:
        """Register quota-limit error.

        Returns:
            bool: True when account was switched due to threshold.
        """
        result = self.register_event(
            provider=provider,
            account_name=account_name,
            mode=mode,
            pool=pool,
            event=RotationEvent.QUOTA_EXHAUSTED,
            model=None,
            group_id=group_id,
        )
        return result.switched

    def register_event(
        self,
        *,
        provider: str,
        account_name: str,
        mode: str,
        pool: list[str],
        event: str,
        model: str | None,
        group_id: str = "g0",
    ) -> EventResult:
        provider = self._normalize_provider_id(provider)
        if mode != "rounding":
            return EventResult(
                decision=RotationDecision.NO_ACTION,
                switched=False,
                all_exhausted=False,
                all_cooldown=False,
            )

        cfg = self._load_provider_config(provider)

        with self._lock:
            state = self._state.setdefault((provider, group_id), _ProviderState())
            if model is not None:
                self._hydrate_exhausted_state(cfg, state, account_name, model)
            self._cleanup_state_for_model_unlocked(state, cfg, model)

            if event == RotationEvent.RATE_LIMIT:
                current = state.consecutive_rate_limit_errors.get(account_name, 0) + 1
                state.consecutive_rate_limit_errors[account_name] = current
                state.consecutive_quota_exhausted_errors[account_name] = 0
                state.successes_on_account.pop(account_name, None)

                logger.info(
                    f"[{provider}] rounding: rate_limit error for {account_name} "
                    f"(consecutive={current}/{cfg.rate_limit_threshold}|model={model}|group={group_id})"
                )

                if current < cfg.rate_limit_threshold:
                    return EventResult(
                        decision=RotationDecision.RETRY_SAME,
                        switched=False,
                        all_exhausted=False,
                        all_cooldown=False,
                    )

                state.consecutive_rate_limit_errors[account_name] = 0
                state.cooldown_until[account_name] = time.time() + cfg.rate_limit_cooldown_seconds
                logger.warning(
                    f"[{provider}] rounding: account {account_name} on cooldown "
                    f"(trigger=RATE_LIMIT|duration={cfg.rate_limit_cooldown_seconds}s|group={group_id})"
                )

                if self._set_next_available_unlocked(
                    state,
                    pool,
                    account_name,
                    model,
                    random_order=cfg.random_order,
                ):
                    next_account = pool[state.next_index]
                    logger.info(
                        f"[{provider}] rounding: switching {account_name} -> {next_account} "
                        f"(trigger=RATE_LIMIT|consecutive_errors={current}|group={group_id})"
                    )
                    return EventResult(
                        decision=RotationDecision.SWITCH_ACCOUNT,
                        switched=True,
                        all_exhausted=False,
                        all_cooldown=False,
                    )

                logger.error(
                    f"[{provider}] rounding: all accounts on cooldown "
                    f"(trigger=RATE_LIMIT|model={model}|group={group_id})"
                )
                return EventResult(
                    decision=RotationDecision.ALL_COOLDOWN,
                    switched=True,
                    all_exhausted=False,
                    all_cooldown=True,
                )

            current = state.consecutive_quota_exhausted_errors.get(account_name, 0) + 1
            state.consecutive_quota_exhausted_errors[account_name] = current
            state.consecutive_rate_limit_errors[account_name] = 0
            state.successes_on_account.pop(account_name, None)

            logger.info(
                f"[{provider}] rounding: quota_exhausted error for {account_name} "
                f"(consecutive={current}/{cfg.quota_exhausted_threshold}|model={model}|group={group_id})"
            )

            if current < cfg.quota_exhausted_threshold:
                return EventResult(
                    decision=RotationDecision.RETRY_SAME,
                    switched=False,
                    all_exhausted=False,
                    all_cooldown=False,
                )

            state.consecutive_quota_exhausted_errors[account_name] = 0
            exhausted_at = datetime.now(tz=timezone.utc)
            until = self._quota_reset_timestamp(cfg, model, exhausted_at=exhausted_at)
            exhausted_for_model = state.quota_exhausted_until.setdefault(account_name, {})
            exhausted_for_model[self._model_key(model)] = until
            self._persist_quota_exhausted_at(cfg, account_name, model, exhausted_at)

            reset_time = datetime.fromtimestamp(until).strftime("%Y-%m-%d %H:%M:%S")
            logger.warning(
                f"[{provider}] rounding: account {account_name} exhausted for model {model} "
                f"(trigger=QUOTA_EXHAUSTED|reset_at={reset_time}|group={group_id})"
            )

            if self._all_exhausted(state, pool, model):
                logger.error(
                    f"[{provider}] rounding: all accounts exhausted "
                    f"(trigger=QUOTA_EXHAUSTED|model={model}|group={group_id})"
                )
                return EventResult(
                    decision=RotationDecision.ALL_EXHAUSTED,
                    switched=True,
                    all_exhausted=True,
                    all_cooldown=False,
                )

            if self._set_next_available_unlocked(
                state,
                pool,
                account_name,
                model,
                random_order=cfg.random_order,
            ):
                next_account = pool[state.next_index]
                logger.info(
                    f"[{provider}] rounding: switching {account_name} -> {next_account} "
                    f"(trigger=QUOTA_EXHAUSTED|consecutive_errors={current}|group={group_id})"
                )
                return EventResult(
                    decision=RotationDecision.SWITCH_ACCOUNT,
                    switched=True,
                    all_exhausted=False,
                    all_cooldown=False,
                )

            logger.error(
                f"[{provider}] rounding: all accounts exhausted or on cooldown "
                f"(trigger=QUOTA_EXHAUSTED|model={model}|group={group_id})"
            )
            return EventResult(
                decision=RotationDecision.ALL_COOLDOWN,
                switched=True,
                all_exhausted=False,
                all_cooldown=True,
            )

    def all_accounts_exhausted(
        self,
        provider: str,
        pool: list[str],
        model: str | None = None,
        group_id: str = "g0",
    ) -> bool:
        provider = self._normalize_provider_id(provider)
        cfg = self._load_provider_config(provider)
        with self._lock:
            state = self._state.setdefault((provider, group_id), _ProviderState())
            for account_name in pool:
                self._hydrate_exhausted_state(cfg, state, account_name, model)
            self._cleanup_state_for_model_unlocked(state, cfg, model)
            return self._all_exhausted(state, pool, model)

    def all_accounts_on_cooldown(
        self,
        provider: str,
        pool: list[str],
        group_id: str = "g0",
    ) -> bool:
        provider = self._normalize_provider_id(provider)
        with self._lock:
            state = self._state.setdefault((provider, group_id), _ProviderState())
            return self._all_cooldown(state, pool)

    def cooldown_wait_seconds(
        self,
        provider: str,
        pool: list[str],
        group_id: str = "g0",
    ) -> int:
        provider = self._normalize_provider_id(provider)
        with self._lock:
            state = self._state.setdefault((provider, group_id), _ProviderState())
            return self._cooldown_wait_seconds(state, pool)

    def _all_exhausted(self, state: _ProviderState, pool: list[str], model: str | None) -> bool:
        if not pool:
            return False
        return all(self._is_exhausted(state, account, model) for account in pool)

    def _all_cooldown(self, state: _ProviderState, pool: list[str]) -> bool:
        if not pool:
            return False
        return all(self._is_on_cooldown(state, account) for account in pool)

    def _is_on_cooldown(self, state: _ProviderState, account_name: str) -> bool:
        until = state.cooldown_until.get(account_name)
        if until is None:
            return False
        return until > time.time()

    def _is_exhausted(self, state: _ProviderState, account_name: str, model: str | None) -> bool:
        by_model = state.quota_exhausted_until.get(account_name, {})
        until = by_model.get(self._model_key(model))
        if until is None:
            return False
        return until > time.time()

    def _set_next_available_unlocked(
        self,
        state: _ProviderState,
        pool: list[str],
        current_account: str,
        model: str | None,
        random_order: bool = False,
    ) -> bool:
        if not pool:
            return False

        if random_order:
            candidates = [
                account
                for account in pool
                if account != current_account
                and not self._is_exhausted(state, account, model)
                and not self._is_on_cooldown(state, account)
            ]
            if not candidates:
                return False
            chosen = random.choice(candidates)
            state.next_index = pool.index(chosen)
            return True

        idx = pool.index(current_account)
        for offset in range(1, len(pool) + 1):
            candidate_idx = (idx + offset) % len(pool)
            candidate = pool[candidate_idx]
            if self._is_exhausted(state, candidate, model):
                continue
            if self._is_on_cooldown(state, candidate):
                continue
            state.next_index = candidate_idx
            return True
        return False

    def _cleanup_state_for_model_unlocked(
        self,
        state: _ProviderState,
        cfg: ProviderConfig,
        model: str | None,
    ) -> None:
        now = time.time()
        for account_name, until in list(state.cooldown_until.items()):
            if until <= now:
                state.cooldown_until.pop(account_name, None)

        model_key = self._model_key(model)
        for account_name, models in list(state.quota_exhausted_until.items()):
            account_models = dict(models)
            for model_name, until in account_models.items():
                if until <= now:
                    models.pop(model_name, None)
            if not models:
                state.quota_exhausted_until.pop(account_name, None)

    def _reset_exhausted_unlocked(self, provider: str, group_id: str) -> None:
        state = self._state.setdefault((provider, group_id), _ProviderState())
        state.quota_exhausted_until.clear()
        state.consecutive_quota_exhausted_errors.clear()

    def _quota_reset_timestamp(
        self,
        cfg: ProviderConfig,
        model: str | None,
        exhausted_at: datetime | None = None,
    ) -> float:
        reset_time = cfg.model_quota_resets.get(model or "") or cfg.model_quota_resets.get("default", "00:00:00")
        days, hours, minutes = _parse_period(reset_time)

        base = exhausted_at or datetime.now(tz=timezone.utc)
        reset_dt = base + timedelta(days=days, hours=hours, minutes=minutes)
        return reset_dt.timestamp()

    def _model_key(self, model: str | None) -> str:
        return model or "<unknown-model>"

    def _normalize_provider_id(self, provider: str) -> str:
        if provider == "gemini":
            return "gemini_cli"
        if provider == "qwen":
            return "qwen_code"
        return provider

    def _resolve_pool(self, cfg: ProviderConfig, group_id: str) -> list[str]:
        if not cfg.groups:
            return cfg.all_accounts
        if group_id in cfg.groups:
            return list(cfg.groups[group_id].accounts)
        if group_id == "g0":
            return cfg.all_accounts
        raise AccountRouterError(f"Unknown group_id '{group_id}' for provider '{cfg.provider}'")

    def _cooldown_wait_seconds(self, state: _ProviderState, pool: list[str]) -> int:
        now = time.time()
        until_values = [state.cooldown_until.get(account) for account in pool]
        active = [value for value in until_values if value is not None and value > now]
        if not active:
            return 0
        return max(0, math.ceil(min(active) - now))

    def _choose_random_available(
        self,
        state: _ProviderState,
        pool: list[str],
        model: str | None,
    ) -> str | None:
        candidates = [
            account
            for account in pool
            if not self._is_exhausted(state, account, model)
            and not self._is_on_cooldown(state, account)
        ]
        if not candidates:
            return None
        return random.choice(candidates)

    def _load_provider_config(self, provider: str) -> ProviderConfig:
        provider = self._normalize_provider_id(provider)
        file_path = self._config_path_for_provider(provider)
        if not file_path.exists():
            raise AccountRouterError(
                f"Accounts config for provider '{provider}' not found: {file_path}"
            )

        with file_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        mode = payload.get("mode", "single")
        if mode not in {"single", "rounding"}:
            raise AccountRouterError(
                f"Invalid mode '{mode}' in {file_path}. Allowed: single|rounding"
            )

        active_account = payload.get("active_account")
        if not active_account:
            raise AccountRouterError(f"Missing active_account in {file_path}")

        all_accounts = payload.get("all_accounts") or []
        if not isinstance(all_accounts, list):
            raise AccountRouterError(f"all_accounts must be list in {file_path}")

        policy_payload = payload.get("rotation_policy") or {}
        if not isinstance(policy_payload, dict):
            raise AccountRouterError(f"rotation_policy must be object in {file_path}")
        rate_limit_threshold = int(policy_payload.get("rate_limit_threshold", 2))
        quota_exhausted_threshold = int(policy_payload.get("quota_exhausted_threshold", 2))
        rate_limit_cooldown_seconds = int(policy_payload.get("rate_limit_cooldown_seconds", 5))
        random_order = bool(policy_payload.get("random_order", False))
        rotate_after_n_successes = int(policy_payload.get("rotate_after_n_successes", 0))

        model_quota_resets = payload.get("model_quota_resets") or {"default": "00:00:00"}
        if not isinstance(model_quota_resets, dict):
            raise AccountRouterError(f"model_quota_resets must be object in {file_path}")
        model_quota_resets = self._validate_model_quota_resets(model_quota_resets, file_path)
        if "default" not in model_quota_resets:
            raise AccountRouterError(f"model_quota_resets must include 'default' in {file_path}")

        accounts_payload = payload.get("accounts") or {}
        if not isinstance(accounts_payload, dict):
            raise AccountRouterError(f"accounts must be object in {file_path}")

        accounts: dict[str, BaseAccount] = {}
        for account_name, account_data in accounts_payload.items():
            if not isinstance(account_data, dict):
                raise AccountRouterError(
                    f"Account '{account_name}' config must be object in {file_path}"
                )
            creds_path = account_data.get("credentials_path")
            if not creds_path:
                raise AccountRouterError(
                    f"Missing credentials_path for account '{account_name}' in {file_path}"
                )

            if provider == "gemini_cli":
                project_id = account_data.get("project_id")
                if not project_id:
                    raise AccountRouterError(
                        f"Missing project_id for gemini account '{account_name}' in {file_path}"
                    )
                accounts[account_name] = GeminiAccount(
                    name=account_name,
                    credentials_path=creds_path,
                    project_id=project_id,
                )
            else:
                accounts[account_name] = BaseAccount(
                    name=account_name,
                    credentials_path=creds_path,
                )

        groups_payload = payload.get("groups") or {}
        if not isinstance(groups_payload, dict):
            raise AccountRouterError(f"groups must be object in {file_path}")
        groups: dict[str, ProviderGroup] = {}
        for group_key, group_data in groups_payload.items():
            if not isinstance(group_data, dict):
                raise AccountRouterError(f"Group '{group_key}' must be object in {file_path}")
            group_accounts = group_data.get("accounts") or []
            if not isinstance(group_accounts, list):
                raise AccountRouterError(
                    f"Group '{group_key}' accounts must be list in {file_path}"
                )
            group_models = group_data.get("models") or []
            if not isinstance(group_models, list):
                raise AccountRouterError(
                    f"Group '{group_key}' models must be list in {file_path}"
                )
            groups[group_key] = ProviderGroup(
                accounts=[str(item) for item in group_accounts],
                models=[str(item) for item in group_models],
            )

        self._validate_disjoint_groups(groups, file_path)

        return ProviderConfig(
            provider=provider,
            mode=mode,
            active_account=active_account,
            all_accounts=all_accounts,
            accounts=accounts,
            rate_limit_threshold=rate_limit_threshold,
            quota_exhausted_threshold=quota_exhausted_threshold,
            rate_limit_cooldown_seconds=rate_limit_cooldown_seconds,
            random_order=random_order,
            rotate_after_n_successes=rotate_after_n_successes,
            model_quota_resets={str(k): str(v) for k, v in model_quota_resets.items()},
            groups=groups,
        )

    def _validate_model_quota_resets(self, model_quota_resets: dict, file_path: Path) -> dict[str, str]:
        parsed: dict[str, str] = {}
        for key, value in model_quota_resets.items():
            value_str = str(value)
            _parse_period(value_str, file_path=file_path)
            parsed[str(key)] = value_str
        return parsed

    def _validate_disjoint_groups(self, groups: dict[str, ProviderGroup], file_path: Path) -> None:
        if not groups:
            return
        seen: dict[str, str] = {}
        for group_key, group in groups.items():
            for account_name in group.accounts:
                previous = seen.get(account_name)
                if previous and previous != group_key:
                    raise AccountRouterError(
                        f"Account '{account_name}' appears in multiple groups ({previous}, {group_key}) in {file_path}"
                    )
                seen[account_name] = group_key

    def _require_account(self, cfg: ProviderConfig, account_name: str) -> BaseAccount:
        account = cfg.accounts.get(account_name)
        if account is None:
            raise AccountRouterError(
                f"Account '{account_name}' is not declared in accounts section"
            )
        return account

    def _config_path_for_provider(self, provider: str) -> Path:
        if provider in {"gemini_cli", "gemini"}:
            return Path(GEMINI_ACCOUNTS_CONFIG_PATH)
        if provider in {"qwen_code", "qwen"}:
            return Path(QWEN_ACCOUNTS_CONFIG_PATH)
        raise AccountRouterError(f"Unsupported provider: {provider}")

    def _persist_quota_exhausted_at(
        self,
        cfg: ProviderConfig,
        account_name: str,
        model: str | None,
        exhausted_at: datetime,
    ) -> None:
        if model is None:
            return
        paths = AccountStatePaths(provider_id=cfg.provider, account_name=account_name, root_dir=Path("."))
        save_quota_exhausted_at(paths, model, exhausted_at)

    def _hydrate_exhausted_state(
        self,
        cfg: ProviderConfig,
        state: _ProviderState,
        account_name: str,
        model: str | None,
    ) -> None:
        if model is None:
            return
        paths = AccountStatePaths(provider_id=cfg.provider, account_name=account_name, root_dir=Path("."))
        exhausted_at = load_quota_exhausted_at(paths, model)
        if exhausted_at is None:
            return
        until = self._quota_reset_timestamp(cfg, model, exhausted_at=exhausted_at)
        exhausted_for_model = state.quota_exhausted_until.setdefault(account_name, {})
        exhausted_for_model[self._model_key(model)] = until


def _parse_period(value: str, file_path: Path | None = None) -> tuple[int, int, int]:
    try:
        day_str, hour_str, minute_str = value.split(":", 2)
        days = int(day_str)
        hours = int(hour_str)
        minutes = int(minute_str)
    except Exception as exc:
        source = f" in {file_path}" if file_path else ""
        raise AccountRouterError(f"Invalid reset period '{value}'{source}. Use DD:HH:MM") from exc

    if days < 0 or not (0 <= hours <= 23) or not (0 <= minutes <= 59):
        source = f" in {file_path}" if file_path else ""
        raise AccountRouterError(
            f"Invalid reset period '{value}'{source}. "
            "Days must be >= 0, hours 0-23, minutes 0-59."
        )
    return days, hours, minutes


quota_account_router = QuotaAccountRouter()

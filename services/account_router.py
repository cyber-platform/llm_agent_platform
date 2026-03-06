from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from config import GEMINI_ACCOUNTS_CONFIG_PATH, QWEN_ACCOUNTS_CONFIG_PATH
from core.logging import get_logger

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
class ProviderConfig:
    provider: str
    mode: str
    active_account: str
    all_accounts: list[str]
    accounts: dict[str, BaseAccount]
    rate_limit_threshold: int
    quota_exhausted_threshold: int
    rate_limit_cooldown_seconds: int
    model_quota_resets: dict[str, str]


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
    consecutive_rate_limit_errors: dict[str, int] = field(default_factory=dict)
    consecutive_quota_exhausted_errors: dict[str, int] = field(default_factory=dict)
    cooldown_until: dict[str, float] = field(default_factory=dict)
    quota_exhausted_until: dict[str, dict[str, float]] = field(default_factory=dict)


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
        self._state: dict[str, _ProviderState] = {}

    def select_account(self, provider: str, model: str | None = None) -> SelectedAccount:
        cfg = self._load_provider_config(provider)
        if cfg.mode == "single":
            account = self._require_account(cfg, cfg.active_account)
            return SelectedAccount(
                provider=provider,
                mode=cfg.mode,
                account=account,
                pool=[cfg.active_account],
                model=model,
            )

        if not cfg.all_accounts:
            raise AccountRouterError(
                f"Provider '{provider}' has mode=rounding but all_accounts is empty"
            )

        with self._lock:
            state = self._state.setdefault(provider, _ProviderState())
            self._cleanup_state_for_model_unlocked(state, cfg, model)

            if self._all_exhausted(state, cfg.all_accounts, model):
                # Fail fast and allow future recovery attempts on next requests.
                logger.warning(
                    f"[{provider}] rounding: all accounts exhausted (model={model})"
                )
                self._reset_exhausted_unlocked(provider)
                raise AllAccountsExhaustedError("all_accounts_exceed_quota")

            if self._all_cooldown(state, cfg.all_accounts):
                logger.warning(
                    f"[{provider}] rounding: all accounts on cooldown (model={model})"
                )
                raise AccountRouterError("all_accounts_on_cooldown")

            start = state.next_index % len(cfg.all_accounts)
            for offset in range(len(cfg.all_accounts)):
                idx = (start + offset) % len(cfg.all_accounts)
                candidate = cfg.all_accounts[idx]
                if self._is_exhausted(state, candidate, model):
                    continue
                if self._is_on_cooldown(state, candidate):
                    continue
                state.next_index = idx
                account = self._require_account(cfg, candidate)
                reason = "rotation" if offset > 0 else "initial"
                logger.info(
                    f"[{provider}] rounding: selected account={candidate} "
                    f"(reason={reason}|attempt={offset + 1}|model={model})"
                )
                return SelectedAccount(
                    provider=provider,
                    mode=cfg.mode,
                    account=account,
                    pool=list(cfg.all_accounts),
                    model=model,
                )

        if self._all_exhausted(state, cfg.all_accounts, model):
            raise AllAccountsExhaustedError("all_accounts_exceed_quota")

        raise AccountRouterError("all_accounts_on_cooldown")

    def register_success(self, provider: str, account_name: str) -> None:
        with self._lock:
            state = self._state.setdefault(provider, _ProviderState())
            state.consecutive_rate_limit_errors[account_name] = 0
            state.consecutive_quota_exhausted_errors[account_name] = 0
            state.cooldown_until.pop(account_name, None)

    def register_quota_limit(
        self,
        provider: str,
        account_name: str,
        mode: str,
        pool: list[str],
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
    ) -> EventResult:
        if mode != "rounding":
            return EventResult(
                decision=RotationDecision.NO_ACTION,
                switched=False,
                all_exhausted=False,
                all_cooldown=False,
            )

        cfg = self._load_provider_config(provider)

        with self._lock:
            state = self._state.setdefault(provider, _ProviderState())
            self._cleanup_state_for_model_unlocked(state, cfg, model)

            if event == RotationEvent.RATE_LIMIT:
                current = state.consecutive_rate_limit_errors.get(account_name, 0) + 1
                state.consecutive_rate_limit_errors[account_name] = current
                state.consecutive_quota_exhausted_errors[account_name] = 0

                logger.info(
                    f"[{provider}] rounding: rate_limit error for {account_name} "
                    f"(consecutive={current}/{cfg.rate_limit_threshold}|model={model})"
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
                    f"(trigger=RATE_LIMIT|duration={cfg.rate_limit_cooldown_seconds}s)"
                )

                if self._set_next_available_unlocked(state, pool, account_name, model):
                    next_account = pool[state.next_index]
                    logger.info(
                        f"[{provider}] rounding: switching {account_name} -> {next_account} "
                        f"(trigger=RATE_LIMIT|consecutive_errors={current})"
                    )
                    return EventResult(
                        decision=RotationDecision.SWITCH_ACCOUNT,
                        switched=True,
                        all_exhausted=False,
                        all_cooldown=False,
                    )

                logger.error(
                    f"[{provider}] rounding: all accounts on cooldown "
                    f"(trigger=RATE_LIMIT|model={model})"
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

            logger.info(
                f"[{provider}] rounding: quota_exhausted error for {account_name} "
                f"(consecutive={current}/{cfg.quota_exhausted_threshold}|model={model})"
            )

            if current < cfg.quota_exhausted_threshold:
                return EventResult(
                    decision=RotationDecision.RETRY_SAME,
                    switched=False,
                    all_exhausted=False,
                    all_cooldown=False,
                )

            state.consecutive_quota_exhausted_errors[account_name] = 0
            until = self._quota_reset_timestamp(cfg, model)
            exhausted_for_model = state.quota_exhausted_until.setdefault(account_name, {})
            exhausted_for_model[self._model_key(model)] = until

            from datetime import datetime
            reset_time = datetime.fromtimestamp(until).strftime("%Y-%m-%d %H:%M:%S")
            logger.warning(
                f"[{provider}] rounding: account {account_name} exhausted for model {model} "
                f"(trigger=QUOTA_EXHAUSTED|reset_at={reset_time})"
            )

            if self._all_exhausted(state, pool, model):
                logger.error(
                    f"[{provider}] rounding: all accounts exhausted "
                    f"(trigger=QUOTA_EXHAUSTED|model={model})"
                )
                return EventResult(
                    decision=RotationDecision.ALL_EXHAUSTED,
                    switched=True,
                    all_exhausted=True,
                    all_cooldown=False,
                )

            if self._set_next_available_unlocked(state, pool, account_name, model):
                next_account = pool[state.next_index]
                logger.info(
                    f"[{provider}] rounding: switching {account_name} -> {next_account} "
                    f"(trigger=QUOTA_EXHAUSTED|consecutive_errors={current})"
                )
                return EventResult(
                    decision=RotationDecision.SWITCH_ACCOUNT,
                    switched=True,
                    all_exhausted=False,
                    all_cooldown=False,
                )

            logger.error(
                f"[{provider}] rounding: all accounts exhausted or on cooldown "
                f"(trigger=QUOTA_EXHAUSTED|model={model})"
            )
            return EventResult(
                decision=RotationDecision.ALL_COOLDOWN,
                switched=True,
                all_exhausted=False,
                all_cooldown=True,
            )

    def all_accounts_exhausted(self, provider: str, pool: list[str], model: str | None = None) -> bool:
        cfg = self._load_provider_config(provider)
        with self._lock:
            state = self._state.setdefault(provider, _ProviderState())
            self._cleanup_state_for_model_unlocked(state, cfg, model)
            return self._all_exhausted(state, pool, model)

    def all_accounts_on_cooldown(self, provider: str, pool: list[str]) -> bool:
        with self._lock:
            state = self._state.setdefault(provider, _ProviderState())
            return self._all_cooldown(state, pool)

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
    ) -> bool:
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
            if model and model_key in models:
                reset_ts = self._quota_reset_timestamp(cfg, model)
                if models[model_key] > reset_ts:
                    models[model_key] = reset_ts
            if not models:
                state.quota_exhausted_until.pop(account_name, None)

    def _reset_exhausted_unlocked(self, provider: str) -> None:
        state = self._state.setdefault(provider, _ProviderState())
        state.quota_exhausted_until.clear()
        state.consecutive_quota_exhausted_errors.clear()

    def _quota_reset_timestamp(self, cfg: ProviderConfig, model: str | None) -> float:
        reset_time = cfg.model_quota_resets.get(model or "") or cfg.model_quota_resets.get("default", "00:00")
        try:
            hour_str, minute_str = reset_time.split(":", 1)
            hour = int(hour_str)
            minute = int(minute_str)
        except Exception as exc:
            raise AccountRouterError(f"Invalid reset time '{reset_time}'. Use HH:MM") from exc

        tz = ZoneInfo("Asia/Vladivostok")
        now = datetime.now(tz)
        reset_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if reset_dt <= now:
            reset_dt = reset_dt + timedelta(days=1)
        return reset_dt.timestamp()

    def _model_key(self, model: str | None) -> str:
        return model or "<unknown-model>"

    def _load_provider_config(self, provider: str) -> ProviderConfig:
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

        model_quota_resets = payload.get("model_quota_resets") or {"default": "00:00"}
        if not isinstance(model_quota_resets, dict):
            raise AccountRouterError(f"model_quota_resets must be object in {file_path}")

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

            if provider == "gemini":
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

        return ProviderConfig(
            provider=provider,
            mode=mode,
            active_account=active_account,
            all_accounts=all_accounts,
            accounts=accounts,
            rate_limit_threshold=rate_limit_threshold,
            quota_exhausted_threshold=quota_exhausted_threshold,
            rate_limit_cooldown_seconds=rate_limit_cooldown_seconds,
            model_quota_resets={str(k): str(v) for k, v in model_quota_resets.items()},
        )

    def _require_account(self, cfg: ProviderConfig, account_name: str) -> BaseAccount:
        account = cfg.accounts.get(account_name)
        if account is None:
            raise AccountRouterError(
                f"Account '{account_name}' is not declared in accounts section"
            )
        return account

    def _config_path_for_provider(self, provider: str) -> Path:
        if provider == "gemini":
            return Path(GEMINI_ACCOUNTS_CONFIG_PATH)
        if provider == "qwen":
            return Path(QWEN_ACCOUNTS_CONFIG_PATH)
        raise AccountRouterError(f"Unsupported provider: {provider}")


quota_account_router = QuotaAccountRouter()

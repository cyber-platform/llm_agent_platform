from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from pathlib import Path

from config import GEMINI_ACCOUNTS_CONFIG_PATH, QWEN_ACCOUNTS_CONFIG_PATH


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


@dataclass(slots=True)
class SelectedAccount:
    provider: str
    mode: str
    account: BaseAccount
    pool: list[str]


@dataclass(slots=True)
class _ProviderState:
    next_index: int = 0
    consecutive_limit_errors: dict[str, int] = field(default_factory=dict)
    exhausted_accounts: set[str] = field(default_factory=set)


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

    def select_account(self, provider: str) -> SelectedAccount:
        cfg = self._load_provider_config(provider)
        if cfg.mode == "single":
            account = self._require_account(cfg, cfg.active_account)
            return SelectedAccount(
                provider=provider,
                mode=cfg.mode,
                account=account,
                pool=[cfg.active_account],
            )

        if not cfg.all_accounts:
            raise AccountRouterError(
                f"Provider '{provider}' has mode=rounding but all_accounts is empty"
            )

        with self._lock:
            state = self._state.setdefault(provider, _ProviderState())
            if self._all_exhausted(state, cfg.all_accounts):
                # Fail fast and allow future recovery attempts on next requests.
                self._reset_exhausted_unlocked(provider)
                raise AllAccountsExhaustedError("all_accounts_exceed_quota")

            start = state.next_index % len(cfg.all_accounts)
            for offset in range(len(cfg.all_accounts)):
                idx = (start + offset) % len(cfg.all_accounts)
                candidate = cfg.all_accounts[idx]
                if candidate in state.exhausted_accounts:
                    continue
                state.next_index = idx
                account = self._require_account(cfg, candidate)
                return SelectedAccount(
                    provider=provider,
                    mode=cfg.mode,
                    account=account,
                    pool=list(cfg.all_accounts),
                )

        raise AllAccountsExhaustedError("all_accounts_exceed_quota")

    def register_success(self, provider: str, account_name: str) -> None:
        with self._lock:
            state = self._state.setdefault(provider, _ProviderState())
            state.consecutive_limit_errors[account_name] = 0
            state.exhausted_accounts.discard(account_name)

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
        if mode != "rounding":
            return False

        with self._lock:
            state = self._state.setdefault(provider, _ProviderState())
            current = state.consecutive_limit_errors.get(account_name, 0) + 1
            state.consecutive_limit_errors[account_name] = current

            if current < 2:
                return False

            state.consecutive_limit_errors[account_name] = 0
            state.exhausted_accounts.add(account_name)

            if self._all_exhausted(state, pool):
                return True

            idx = pool.index(account_name)
            for offset in range(1, len(pool) + 1):
                candidate_idx = (idx + offset) % len(pool)
                candidate = pool[candidate_idx]
                if candidate in state.exhausted_accounts:
                    continue
                state.next_index = candidate_idx
                return True

            return True

    def all_accounts_exhausted(self, provider: str, pool: list[str]) -> bool:
        with self._lock:
            state = self._state.setdefault(provider, _ProviderState())
            return self._all_exhausted(state, pool)

    def _all_exhausted(self, state: _ProviderState, pool: list[str]) -> bool:
        if not pool:
            return False
        return all(account in state.exhausted_accounts for account in pool)

    def _reset_exhausted_unlocked(self, provider: str) -> None:
        state = self._state.setdefault(provider, _ProviderState())
        state.exhausted_accounts.clear()
        state.consecutive_limit_errors.clear()

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


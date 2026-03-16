from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Final

from core.logging import get_logger

logger = get_logger(__name__)

_LAST_USED_FILE: Final[str] = "last_used_at.json"
_QUOTA_EXHAUSTED_DIR: Final[str] = "quota_exhausted"


@dataclass(slots=True)
class AccountStatePaths:
    provider_id: str
    account_name: str
    root_dir: Path

    @property
    def account_dir(self) -> Path:
        return self.root_dir / "secrets" / self.provider_id / "state" / self.account_name

    @property
    def last_used_path(self) -> Path:
        return self.account_dir / _LAST_USED_FILE

    @property
    def quota_exhausted_dir(self) -> Path:
        return self.account_dir / _QUOTA_EXHAUSTED_DIR

    def quota_exhausted_path(self, model: str) -> Path:
        safe_model = _sanitize_model_key(model)
        return self.quota_exhausted_dir / f"{safe_model}.json"


def load_last_used_at(paths: AccountStatePaths) -> datetime | None:
    payload = _read_json(paths.last_used_path)
    if not payload:
        return None
    raw = payload.get("last_used_at")
    if not isinstance(raw, str):
        return None
    return _parse_datetime(raw)


def save_last_used_at(paths: AccountStatePaths, when: datetime) -> None:
    payload = {
        "version": 1,
        "last_used_at": _format_datetime(when),
    }
    _write_json(paths.last_used_path, payload)


def load_quota_exhausted_at(paths: AccountStatePaths, model: str) -> datetime | None:
    payload = _read_json(paths.quota_exhausted_path(model))
    if not payload:
        return None
    raw = payload.get("quota_exhausted_at")
    if not isinstance(raw, str):
        return None
    return _parse_datetime(raw)


def save_quota_exhausted_at(paths: AccountStatePaths, model: str, when: datetime) -> None:
    payload = {
        "version": 1,
        "quota_exhausted_at": _format_datetime(when),
    }
    _write_json(paths.quota_exhausted_path(model), payload)


def _write_json(file_path: Path, payload: dict) -> None:
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        with tmp_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        tmp_path.replace(file_path)
    except Exception as exc:
        logger.warning(f"[state] Failed to write state file {file_path}: {exc}")


def _read_json(file_path: Path) -> dict | None:
    if not file_path.exists():
        return None
    try:
        with file_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as exc:
        logger.warning(f"[state] Failed to read state file {file_path}: {exc}")
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _format_datetime(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_datetime(value: str) -> datetime | None:
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        parsed = datetime.fromisoformat(value)
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _sanitize_model_key(model: str) -> str:
    return model.replace("/", "__")

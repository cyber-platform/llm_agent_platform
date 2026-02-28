from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Iterable

from config import CLOUD_CODE_ENDPOINT
from services.http_pool import get_http_client

_CAPTURE_DIR = Path(os.environ.get("PARITY_CAPTURE_DIR", "artifacts/parity"))
_CAPTURE_ENABLED = os.environ.get("PARITY_CAPTURE_ENABLED", "false").lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def build_quota_payload(
    *,
    model: str,
    project: str,
    request_payload: dict[str, Any],
    user_prompt_id: str,
    session_id: str | None,
) -> dict[str, Any]:
    request_data = dict(request_payload)
    if session_id:
        request_data["session_id"] = session_id

    return {
        "model": model,
        "project": project,
        "user_prompt_id": user_prompt_id,
        "request": request_data,
    }


def generate_user_prompt_id() -> str:
    return str(uuid.uuid4())


def generate_session_id() -> str:
    return str(uuid.uuid4())


def quota_headers(token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def quota_url(stream: bool) -> str:
    return f"{CLOUD_CODE_ENDPOINT}:{'streamGenerateContent' if stream else 'generateContent'}"


def send_generate(token: str, payload: dict[str, Any]):
    client = get_http_client()
    _capture("proxy_request_generate", payload)
    response = client.post(
        quota_url(stream=False),
        headers=quota_headers(token),
        json=payload,
    )
    _capture_response("proxy_response_generate", response.status_code, response.text)
    return response


def stream_generate_lines(token: str, payload: dict[str, Any]) -> Iterable[str]:
    client = get_http_client()
    _capture("proxy_request_stream", payload)
    with client.stream(
        "POST",
        quota_url(stream=True),
        headers=quota_headers(token),
        json=payload,
        params={"alt": "sse"},
    ) as response:
        if response.status_code != 200:
            body = response.read().decode(errors="replace")
            _capture_response("proxy_response_stream_error", response.status_code, body)
            raise RuntimeError(f"{response.status_code}:{body}")

        for line in response.iter_lines():
            if not line:
                continue
            text_line = line.decode() if isinstance(line, bytes) else line
            _capture_line("proxy_response_stream_line", text_line)
            yield text_line


def unwrap_cloud_code_response(data: dict[str, Any]) -> dict[str, Any]:
    return data.get("response", data)


def parse_cloud_code_sse_line(line: str) -> dict[str, Any] | None:
    if not line.startswith("data: "):
        return None

    raw = line[6:].strip()
    if raw == "[DONE]":
        return {"done": True}

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        return None

    return unwrap_cloud_code_response(parsed)


def _capture(kind: str, payload: dict[str, Any]) -> None:
    if not _CAPTURE_ENABLED:
        return

    _CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    file = _CAPTURE_DIR / f"{int(time.time() * 1000)}_{kind}.json"
    with file.open("w", encoding="utf-8") as f:
        json.dump(_sanitize(payload), f, ensure_ascii=False, indent=2)


def _capture_response(kind: str, status: int, body: str) -> None:
    if not _CAPTURE_ENABLED:
        return

    _CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    file = _CAPTURE_DIR / f"{int(time.time() * 1000)}_{kind}.json"
    payload = {
        "status": status,
        "body": body,
    }
    with file.open("w", encoding="utf-8") as f:
        json.dump(_sanitize(payload), f, ensure_ascii=False, indent=2)


def _capture_line(kind: str, line: str) -> None:
    if not _CAPTURE_ENABLED:
        return

    _CAPTURE_DIR.mkdir(parents=True, exist_ok=True)
    file = _CAPTURE_DIR / f"{int(time.time() * 1000)}_{kind}.txt"
    with file.open("w", encoding="utf-8") as f:
        f.write(line)


def _sanitize(data: Any) -> Any:
    if isinstance(data, dict):
        out: dict[str, Any] = {}
        for key, value in data.items():
            key_lower = key.lower()
            if key_lower in {"authorization", "token", "access_token", "refresh_token", "client_secret"}:
                out[key] = "***redacted***"
            else:
                out[key] = _sanitize(value)
        return out

    if isinstance(data, list):
        return [_sanitize(v) for v in data]

    return data

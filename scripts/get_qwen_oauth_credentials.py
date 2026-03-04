from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Позволяет запускать скрипт напрямую: `python scripts/get_qwen_oauth_credentials.py`
# и `uv run scripts/get_qwen_oauth_credentials.py`.
if __package__ is None or __package__ == "":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from auth.qwen_oauth import (
    QwenOAuthError,
    generate_pkce_pair,
    normalize_qwen_credentials,
    poll_device_token,
    request_device_authorization,
    write_qwen_credentials,
)


def main() -> None:
    """Run Qwen OAuth device flow and persist credentials.

    The script writes credentials to `secrets/user_qwen_credentials.json`.
    """
    print("=== Qwen OAuth Credentials Generator ===")
    logger.info("Starting OAuth device authorization flow...")

    print("[INFO] Generating PKCE pair...")
    verifier, challenge = generate_pkce_pair()
    logger.debug(f"PKCE challenge generated: {challenge[:20]}...")

    print("[INFO] Requesting device authorization...")
    device = request_device_authorization(challenge)
    logger.info(f"Device code received, expires_in={device.get('expires_in', 'unknown')}")

    verification_uri_complete = device.get("verification_uri_complete")
    verification_uri = device.get("verification_uri")
    user_code = device.get("user_code")

    if verification_uri_complete:
        print("\n[STEP] Open this URL in your browser and complete authorization:")
        print(verification_uri_complete)
        if not _is_true_env("NO_BROWSER"):
            _try_open_browser(verification_uri_complete)
    else:
        print("\n[STEP] Open this URL in your browser and enter user code:")
        print(verification_uri or "<missing verification_uri>")
        if user_code:
            print(f"User code: {user_code}")

    timeout_seconds = int(device.get("expires_in", 600))
    print(f"\n[WAIT] Waiting for authorization (timeout: {timeout_seconds}s)...")
    print("[INFO] The script will poll the server every 2 seconds.")
    print("[INFO] Do NOT press Ctrl+C unless you want to cancel.\n")

    logger.info(f"Starting token polling with timeout={timeout_seconds}s")

    try:
        token_data = poll_device_token(
            device_code=device["device_code"],
            code_verifier=verifier,
            timeout_seconds=timeout_seconds,
        )
    except Exception:
        # Перехватываем и логируем перед пробросом
        logger.exception("Token polling failed")
        raise

    logger.info("Token received, normalizing credentials...")
    normalized = normalize_qwen_credentials(token_data)
    file_path = write_qwen_credentials(normalized)

    print(f"\n[SUCCESS] Credentials saved to '{file_path}'")
    print("[INFO] You can now use qwen quota model via proxy.")
    logger.info(f"Credentials saved to {file_path}")


def _is_true_env(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _try_open_browser(url: str) -> None:
    """Best-effort browser opener for Linux/macOS/Windows."""
    commands = [
        ["xdg-open", url],
        ["gio", "open", url],
        ["open", url],
        ["cmd", "/c", "start", "", url],
    ]

    for cmd in commands:
        try:
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("[INFO] Browser open requested automatically.")
            return
        except Exception:
            continue

    print("[WARN] Could not auto-open browser. Open URL manually.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        # Это реальное прерывание пользователем (Ctrl+C)
        print("\n[INFO] Authorization interrupted by user (Ctrl+C).")
        logger.info("KeyboardInterrupt: User pressed Ctrl+C")
        sys.exit(130)  # Стандартный exit code для прерывания по Ctrl+C
    except QwenOAuthError as exc:
        print(f"\n[ERROR] OAuth flow failed: {exc}")
        logger.error(f"QwenOAuthError: {exc}")
        sys.exit(1)
    except Exception as exc:
        # Важно: логируем полную трассировку для диагностики
        logger.exception(f"Unexpected failure: {type(exc).__name__}: {exc}")
        print(f"\n[ERROR] Unexpected failure: {type(exc).__name__}: {exc}")
        print("[DEBUG] Check logs above for full traceback.")
        sys.exit(1)

import os


def _env_str(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _env_flag(name: str, default: str = "false") -> bool:
    return _env_str(name, default).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

# --- Logging Configuration ---
LOG_LEVEL = _env_str("LOG_LEVEL", "INFO")
LOG_DIR = _env_str("LOG_DIR", "./logs")

# --- Configuration ---
USER_GEMINI_CREDS_PATH = _env_str(
    "USER_GEMINI_CREDS_PATH",
    "secrets/user_gemini_credentials.json",
)
USER_QWEN_CREDS_PATH = _env_str(
    "USER_QWEN_CREDS_PATH",
    "secrets/user_qwen_credentials.json",
)
GEMINI_ACCOUNTS_CONFIG_PATH = _env_str(
    "GEMINI_ACCOUNTS_CONFIG_PATH",
    "secrets/gemini_accounts_config.json",
)
QWEN_ACCOUNTS_CONFIG_PATH = _env_str(
    "QWEN_ACCOUNTS_CONFIG_PATH",
    "secrets/qwen_accounts_config.json",
)
SERVICE_ACCOUNT_PATH = _env_str("SERVICE_ACCOUNT_PATH", "secrets/service_account.json")

# --- Gemini CLI Emulation Constants ---
GEMINI_CLI_CLIENT_ID = _env_str("GEMINI_CLI_CLIENT_ID")
GEMINI_CLI_CLIENT_SECRET = _env_str("GEMINI_CLI_CLIENT_SECRET")
CLOUD_CODE_ENDPOINT = _env_str(
    "CLOUD_CODE_ENDPOINT",
    "https://cloudcode-pa.googleapis.com/v1internal",
)
STRICT_CLI_PARITY = _env_flag("STRICT_CLI_PARITY", "true")
DEFAULT_QUOTA_MODEL = _env_str("DEFAULT_QUOTA_MODEL", "gemini-3-flash-preview-quota")

# --- Qwen OAuth / quota constants ---
QWEN_OAUTH_CLIENT_ID = _env_str("QWEN_OAUTH_CLIENT_ID")
QWEN_OAUTH_SCOPE = _env_str("QWEN_OAUTH_SCOPE", "openid profile email model.completion")
QWEN_OAUTH_DEVICE_CODE_ENDPOINT = _env_str(
    "QWEN_OAUTH_DEVICE_CODE_ENDPOINT",
    "https://chat.qwen.ai/api/v1/oauth2/device/code",
)
QWEN_OAUTH_TOKEN_ENDPOINT = _env_str(
    "QWEN_OAUTH_TOKEN_ENDPOINT",
    "https://chat.qwen.ai/api/v1/oauth2/token",
)
QWEN_DEFAULT_RESOURCE_URL = _env_str(
    "QWEN_DEFAULT_RESOURCE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode",
)
QWEN_QUOTA_MODELS = [
    model.strip()
    for model in _env_str("QWEN_QUOTA_MODELS", "qwen-coder-model-quota").split(",")
    if model.strip()
]

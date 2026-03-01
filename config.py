import os

# --- Configuration ---
USER_GEMINI_CREDS_PATH = os.environ.get(
    "USER_GEMINI_CREDS_PATH",
    "secrets/user_gemini_credentials.json",
)
USER_QWEN_CREDS_PATH = os.environ.get(
    "USER_QWEN_CREDS_PATH",
    "secrets/user_qwen_credentials.json",
)
GEMINI_ACCOUNTS_CONFIG_PATH = os.environ.get(
    "GEMINI_ACCOUNTS_CONFIG_PATH",
    "secrets/gemini_accounts_config.json",
)
QWEN_ACCOUNTS_CONFIG_PATH = os.environ.get(
    "QWEN_ACCOUNTS_CONFIG_PATH",
    "secrets/qwen_accounts_config.json",
)
SERVICE_ACCOUNT_PATH = os.environ.get("SERVICE_ACCOUNT_PATH", "secrets/service_account.json")

# --- Gemini CLI Emulation Constants ---
GEMINI_CLI_CLIENT_ID = os.environ.get(
    "GEMINI_CLI_CLIENT_ID",
    "681255809395-oo8ft2oprdrnp9e3aqf6av3hmdib135j.apps.googleusercontent.com",
)
GEMINI_CLI_CLIENT_SECRET = os.environ.get(
    "GEMINI_CLI_CLIENT_SECRET",
    "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",
)
CLOUD_CODE_ENDPOINT = os.environ.get(
    "CLOUD_CODE_ENDPOINT",
    "https://cloudcode-pa.googleapis.com/v1internal",
)
STRICT_CLI_PARITY = os.environ.get("STRICT_CLI_PARITY", "true").lower() in {
    "1",
    "true",
    "yes",
    "on",
}
DEFAULT_QUOTA_MODEL = os.environ.get("DEFAULT_QUOTA_MODEL", "gemini-3-flash-preview-quota")

# --- Qwen OAuth / quota constants ---
QWEN_OAUTH_CLIENT_ID = os.environ.get("QWEN_OAUTH_CLIENT_ID", "f0304373b74a44d2b584a3fb70ca9e56")
QWEN_OAUTH_SCOPE = os.environ.get("QWEN_OAUTH_SCOPE", "openid profile email model.completion")
QWEN_OAUTH_DEVICE_CODE_ENDPOINT = os.environ.get(
    "QWEN_OAUTH_DEVICE_CODE_ENDPOINT",
    "https://chat.qwen.ai/api/v1/oauth2/device/code",
)
QWEN_OAUTH_TOKEN_ENDPOINT = os.environ.get(
    "QWEN_OAUTH_TOKEN_ENDPOINT",
    "https://chat.qwen.ai/api/v1/oauth2/token",
)
QWEN_DEFAULT_RESOURCE_URL = os.environ.get(
    "QWEN_DEFAULT_RESOURCE_URL",
    "https://dashscope.aliyuncs.com/compatible-mode",
)
QWEN_QUOTA_MODELS = [
    model.strip()
    for model in os.environ.get("QWEN_QUOTA_MODELS", "qwen-coder-model-quota").split(",")
    if model.strip()
]

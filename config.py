import os

# --- Configuration ---
USER_CREDS_PATH = os.environ.get("USER_CREDS_PATH", "secrets/user_credentials.json")
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

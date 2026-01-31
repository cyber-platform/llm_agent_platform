import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow

# --- Gemini CLI Constants ---
# These are the official Client ID and Secret used by Gemini CLI / Cloud Code.
# Using them allows us to access the "User Quota" (1500 req/day) instead of the "Project Quota" (20 req/day).
GEMINI_CLI_CLIENT_ID = '681255809395-oo8ft2oprdrnp9e3aqf6av3hmdib135j.apps.googleusercontent.com'
GEMINI_CLI_CLIENT_SECRET = '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'

# Scopes required for Cloud Code API
SCOPES = [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile'
]

def main():
    # Fix for "Scope has changed" error: Google adds 'openid' scope automatically
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    
    print("=== Google OAuth 2.0 Credentials Generator (Gemini CLI Emulation) ===")
    print("\n[INFO] This script will authenticate you using the official Gemini CLI Client ID.")
    print("       This is required to access the 1500 req/day user quota.")
    
    # Create client config dictionary manually instead of loading from file
    client_config = {
        "installed": {
            "client_id": GEMINI_CLI_CLIENT_ID,
            "client_secret": GEMINI_CLI_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost:8080/"]
        }
    }

    try:
        # Initialize flow with the manual config
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        
        print("\n[WAIT] Ожидание подтверждения в браузере...")
        auth_creds = flow.run_local_server(
            port=8080,
            host='localhost',
            success_message='Авторизация успешна! Вы можете закрыть это окно и вернуться в терминал.'
        )
        
        # Save credentials in the format expected by main.py
        creds = {
            "client_id": GEMINI_CLI_CLIENT_ID,
            "client_secret": GEMINI_CLI_CLIENT_SECRET,
            "refresh_token": auth_creds.refresh_token,
            "type": "authorized_user"
        }

        os.makedirs('secrets', exist_ok=True)
        with open('secrets/user_credentials.json', 'w') as f:
            json.dump(creds, f, indent=2)
            
        print("\n[SUCCESS] Credentials saved to 'secrets/user_credentials.json'")
        print("You can now restart your Docker container to apply changes.")
        
    except Exception as e:
        print(f"\n[ERROR] OAuth flow failed: {e}")

if __name__ == '__main__':
    main()
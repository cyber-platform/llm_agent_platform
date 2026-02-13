import os
import json
import time
import threading
import sys
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from config import USER_CREDS_PATH, SERVICE_ACCOUNT_PATH, GEMINI_CLI_CLIENT_ID, GEMINI_CLI_CLIENT_SECRET

# Global state for credentials - use a dict to store to avoid module-level reference issues
_auth_state = {
    'user_creds': None,
    'auth_lock': threading.Lock()
}

def get_user_creds():
    """Get current user credentials"""
    return _auth_state['user_creds']

def set_user_creds(creds):
    """Set user credentials"""
    with _auth_state['auth_lock']:
        _auth_state['user_creds'] = creds

def get_auth_lock():
    """Get auth lock"""
    return _auth_state['auth_lock']

def initialize_auth():
    """Initializes OAuth credentials on startup"""
    global user_creds
    try:
        if os.path.exists(USER_CREDS_PATH):
            with open(USER_CREDS_PATH, 'r') as f:
                info = json.load(f)
            
            # Use Gemini CLI Client ID/Secret if not present in the file
            client_id = info.get('client_id', GEMINI_CLI_CLIENT_ID)
            client_secret = info.get('client_secret', GEMINI_CLI_CLIENT_SECRET)

            creds = Credentials(
                token=None,
                refresh_token=info['refresh_token'],
                token_uri="https://oauth2.googleapis.com/token",
                client_id=client_id,
                client_secret=client_secret
            )
            
            creds.refresh(Request())
            set_user_creds(creds)
            print(f"[AUTH] User OAuth token initialized (Gemini CLI Mode).", flush=True)
            return True
        else:
            print(f"[AUTH] Error: {USER_CREDS_PATH} not found!", flush=True)
            return False
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[AUTH] User initialization failed: {e}", flush=True)
        return False

def refresh_user_creds():
    """Refreshes OAuth credentials in the background using Gemini CLI client ID"""
    
    while True:
        sleep_time = 3000
        try:
            if os.path.exists(USER_CREDS_PATH):
                with open(USER_CREDS_PATH, 'r') as f:
                    info = json.load(f)
                
                # Use Gemini CLI Client ID/Secret if not present in the file
                client_id = info.get('client_id', GEMINI_CLI_CLIENT_ID)
                client_secret = info.get('client_secret', GEMINI_CLI_CLIENT_SECRET)

                creds = Credentials(
                    token=None,
                    refresh_token=info['refresh_token'],
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=client_id,
                    client_secret=client_secret
                )
                
                creds.refresh(Request())
                set_user_creds(creds)
                print(f"[AUTH] User OAuth token refreshed (Gemini CLI Mode).", flush=True)
            else:
                print(f"[AUTH] Error: {USER_CREDS_PATH} not found!", flush=True)
                sleep_time = 60 # Check again in a minute if file missing
        except Exception as e:
            print(f"[AUTH] User refresh failed: {e}", flush=True)
            sleep_time = 30 # Retry sooner on failure
        time.sleep(sleep_time)

def get_vertex_token():
    """Gets an access token for Vertex AI using Service Account"""
    if not os.path.exists(SERVICE_ACCOUNT_PATH):
        return None
    creds = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_PATH, 
        scopes=['https://www.googleapis.com/auth/cloud-platform']
    )
    creds.refresh(Request())
    return creds.token
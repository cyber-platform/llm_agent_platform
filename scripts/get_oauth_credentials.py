import os
import json
import socket
from urllib.parse import parse_qs, urlparse
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


def _is_true_env(name: str) -> bool:
    return os.environ.get(name, '').strip().lower() in {'1', 'true', 'yes', 'on'}


def _get_callback_port() -> int:
    port_env = os.environ.get('OAUTH_CALLBACK_PORT')
    if port_env:
        try:
            port = int(port_env)
        except ValueError as exc:
            raise ValueError(f"Invalid OAUTH_CALLBACK_PORT: {port_env}") from exc

        if not (1 <= port <= 65535):
            raise ValueError(f"Invalid OAUTH_CALLBACK_PORT: {port_env}")
        return port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('', 0))
        return int(sock.getsockname()[1])


def _get_bind_addr() -> str:
    # Как и в gemini-cli: redirect URI остаётся loopback (127.0.0.1),
    # но bind-адрес callback сервера можно переопределить env-переменной.
    return os.environ.get('OAUTH_CALLBACK_HOST', '127.0.0.1')


def _extract_code_from_input(value: str) -> str:
    raw = value.strip()
    if not raw:
        raise ValueError('Пустой ввод.')

    if raw.startswith('http://') or raw.startswith('https://'):
        parsed = urlparse(raw)
        query = parse_qs(parsed.query)
        code = query.get('code', [None])[0]
        if not code:
            raise ValueError('В callback URL не найден параметр code.')
        return code

    return raw


def _authorize_manual(flow: InstalledAppFlow, open_browser: bool) -> object:
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        prompt='consent',
    )

    print('\n[MANUAL] Откройте ссылку ниже и завершите авторизацию:')
    print(auth_url)

    if open_browser:
        print('[MANUAL] Если браузер открылся автоматически, дождитесь редиректа и скопируйте URL из адресной строки.')

    print('[MANUAL] Вставьте полный callback URL (http://127.0.0.1:PORT/?code=...) или только значение code:')
    callback_or_code = input('> ').strip()
    code = _extract_code_from_input(callback_or_code)

    flow.fetch_token(code=code)
    return flow.credentials

def main():
    # Fix for "Scope has changed" error: Google adds 'openid' scope automatically
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    
    print("=== Google OAuth 2.0 Credentials Generator (Gemini CLI Emulation) ===")
    print("\n[INFO] This script will authenticate you using the official Gemini CLI Client ID.")
    print("       This is required to access the 1500 req/day user quota.")

    callback_port = _get_callback_port()
    bind_addr = _get_bind_addr()
    no_browser = _is_true_env('NO_BROWSER')
    redirect_uri = f"http://127.0.0.1:{callback_port}/"
    
    # Create client config dictionary manually instead of loading from file
    client_config = {
        "installed": {
            "client_id": GEMINI_CLI_CLIENT_ID,
            "client_secret": GEMINI_CLI_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri]
        }
    }

    try:
        # Initialize flow with the manual config
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        flow.redirect_uri = redirect_uri
        
        print("\n[WAIT] Ожидание подтверждения в браузере...")
        print(f"[INFO] Callback bind: {bind_addr}:{callback_port} | Redirect URI: {redirect_uri}")
        if no_browser:
            print("[INFO] NO_BROWSER=true: ссылка будет выведена в терминал, откройте её вручную.")

        if no_browser:
            auth_creds = _authorize_manual(flow, open_browser=False)
        else:
            try:
                auth_creds = flow.run_local_server(
                    host='127.0.0.1',
                    bind_addr=bind_addr,
                    port=callback_port,
                    open_browser=True,
                    timeout_seconds=300,
                    prompt='consent',
                    success_message='Авторизация успешна! Вы можете закрыть это окно и вернуться в терминал.'
                )
            except TimeoutError:
                print("\n[WARN] Локальный callback не был получен за 300 секунд. Перехожу в ручной режим.")
                auth_creds = _authorize_manual(flow, open_browser=False)

        if not auth_creds.refresh_token:
            raise RuntimeError(
                'Google не вернул refresh_token. Попробуйте отозвать доступ приложения "Google Cloud Code" '
                'в Google Account permissions и пройти авторизацию заново.'
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

    except KeyboardInterrupt:
        print("\n[INFO] Авторизация прервана пользователем.")
    except TimeoutError:
        print("\n[ERROR] OAuth flow timed out (300s). Попробуйте снова или используйте NO_BROWSER=true.")
    except Exception as e:
        print(f"\n[ERROR] OAuth flow failed: {e}")

if __name__ == '__main__':
    main()

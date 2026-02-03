import os
import json
import time
import threading
import httpx
from flask import Flask, request, Response, stream_with_context
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.oauth2 import service_account

app = Flask(__name__)

# --- Configuration ---
USER_CREDS_PATH = 'secrets/user_credentials.json'
SERVICE_ACCOUNT_PATH = 'secrets/service_account.json'

# --- Gemini CLI Emulation Constants ---
GEMINI_CLI_CLIENT_ID = '681255809395-oo8ft2oprdrnp9e3aqf6av3hmdib135j.apps.googleusercontent.com'
GEMINI_CLI_CLIENT_SECRET = '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'
CLOUD_CODE_ENDPOINT = "https://cloudcode-pa.googleapis.com/v1internal"

# Global state for credentials
user_creds = None
auth_lock = threading.Lock()
project_id_cache = None

def refresh_user_creds():
    """Refreshes OAuth credentials in the background using Gemini CLI client ID"""
    global user_creds
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
                with auth_lock:
                    user_creds = creds
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

def discover_project_id(token):
    """
    Discovers the Google Cloud project ID associated with the user's account.
    Prioritizes environment variables, then attempts to fetch user info.
    Does NOT use Cloud Code API for discovery to avoid circular dependency on API activation.
    """
    global project_id_cache
    if project_id_cache:
        return project_id_cache

    # Check env var first
    if os.environ.get("GOOGLE_CLOUD_PROJECT"):
        project_id_cache = os.environ.get("GOOGLE_CLOUD_PROJECT")
        print(f"[AUTH] Using Project ID from env: {project_id_cache}", flush=True)
        return project_id_cache

    # Fallback to a hardcoded default if known, or try to infer from user info
    # For now, we strongly rely on the env var because the Cloud Code API discovery endpoint
    # itself requires the API to be enabled, creating a chicken-and-egg problem.
    
    print("[AUTH] Warning: GOOGLE_CLOUD_PROJECT env var not set. Using fallback project discovery.", flush=True)
    
    # Try to get project from userinfo (not standard, but sometimes helpful for debugging)
    # or just return a placeholder that might work if the user has a default project set
    # in their gcloud config (though we can't access gcloud config here directly).
    
    # Returning None here will cause an error downstream, prompting the user to set the env var.
    return None

def map_model_name(name):
    """Maps proxy model names to real Google model IDs (January 2026)"""
    mapping = {
        # Quota Group (OAuth)
        'gemini-3-pro-preview-quota': 'gemini-3-pro-preview',
        'gemini-3-flash-preview-quota': 'gemini-3-flash-preview',
        'gemini-2.5-pro-quota': 'gemini-2.5-pro',
        'gemini-2.5-flash-quota': 'gemini-2.5-flash',
        'gemini-2.5-flash-lite-quota': 'gemini-2.5-flash-lite',
        
        # Vertex Group (Credits)
        'gemini-3-pro-preview-vertex': 'gemini-3-pro-preview',
        'gemini-3-flash-preview-vertex': 'gemini-3-flash-preview',
        'gemini-2.5-pro-vertex': 'gemini-2.5-pro',
        'gemini-2.5-flash-vertex': 'gemini-2.5-flash',
        'gemini-2.5-flash-lite-vertex': 'gemini-2.5-flash-lite',
        
        # Specialized
        'gemini-3-pro-image-vertex': 'gemini-3-pro-image-preview',
        'gemini-2.5-flash-image-vertex': 'gemini-2.5-flash-image',
        'nano-banana': 'gemini-2.5-flash-image'
    }
    return mapping.get(name, name)

def clean_gemini_schema(schema):
    """
    Очищает JSON Schema для совместимости с Gemini API (Google Cloud / Vertex AI).
    1. Преобразует type: ["string", "null"] -> type: "string"
    2. Удаляет $schema
    3. Удаляет additionalProperties (если вызывает проблемы, но пока оставим, если false)
    """
    if not isinstance(schema, dict):
        return schema
    
    new_schema = schema.copy()
    
    # 1. Fix type being a list
    if 'type' in new_schema:
        if isinstance(new_schema['type'], list):
            # Take the first non-null type
            types = [t for t in new_schema['type'] if t != 'null']
            if types:
                new_schema['type'] = types[0]
            else:
                # Fallback if only null or empty
                new_schema['type'] = 'STRING'
    
    # 2. Remove $schema
    if '$schema' in new_schema:
        del new_schema['$schema']
        
    # Recurse
    if 'properties' in new_schema:
        new_schema['properties'] = {k: clean_gemini_schema(v) for k, v in new_schema['properties'].items()}
    
    if 'items' in new_schema:
        new_schema['items'] = clean_gemini_schema(new_schema['items'])
        
    return new_schema

def transform_openai_to_gemini(messages):
    """
    Преобразует сообщения из формата OpenAI в формат Gemini.
    Поддерживает:
    - system (переносится в system_instruction или prepend к первому user)
    - user (текст и массивы контента)
    - assistant (текст)
    """
    contents = []
    system_instruction = None
    
    for m in messages:
        role = m.get('role')
        raw_content = m.get('content')
        
        text_parts = []
        if isinstance(raw_content, str):
            text_parts.append({"text": raw_content})
        elif isinstance(raw_content, list):
            for part in raw_content:
                if isinstance(part, dict):
                    if part.get("type") == "text":
                        text_parts.append({"text": part.get("text", "")})
                    # TODO: Добавить поддержку image_url для мультимодальности
                elif isinstance(part, str):
                    text_parts.append({"text": part})

        if role == 'system' or role == 'developer': # OpenAI o1/o3 использует developer
            current_text = "".join([p["text"] for p in text_parts])
            if system_instruction:
                system_instruction += "\n" + current_text
            else:
                system_instruction = current_text
        else:
            # Gemini использует роли 'user' и 'model'
            gemini_role = 'user' if role == 'user' else 'model'
            contents.append({
                "role": gemini_role,
                "parts": text_parts
            })
            
    return contents, system_instruction

def create_openai_error(message, type="server_error", code=500):
    """Формирует ошибку в формате OpenAI"""
    return json.dumps({
        "error": {
            "message": message,
            "type": type,
            "param": None,
            "code": code
        }
    }, ensure_ascii=False)

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    try:
        data = request.json
        raw_model = data.get('model', 'gemini-3-flash-preview-quota')
        target_model = map_model_name(raw_model)
        messages = data.get('messages', [])
        stream = data.get('stream', False)
        stream_options = data.get('stream_options', {})
        include_usage = stream_options.get('include_usage', False) if stream else False
        
        print(f"[REQ] Model: {raw_model} -> {target_model} | Stream: {stream} | Usage: {include_usage}", flush=True)

        contents, system_instruction = transform_openai_to_gemini(messages)
        
        # Базовая конфигурация для Gemini
        # Поддержка reasoning (thinking)
        reasoning_effort = data.get('reasoning_effort')
        max_thinking_tokens = data.get('modelMaxThinkingTokens') or data.get('max_completion_tokens')
        
        gemini_config = {
            "temperature": data.get('temperature', 0.7),
            "maxOutputTokens": data.get('max_tokens', 4096),
        }

        if reasoning_effort or max_thinking_tokens or data.get('enableReasoningEffort'):
            thinking_config = {
                "includeThoughts": True
            }
            if max_thinking_tokens:
                thinking_config["thinkingBudget"] = int(max_thinking_tokens)
            
            # Для Gemini 3 можно прокидывать thinking_level, но пока ограничимся бюджетом
            # так как он более универсален для 2.5/3.0
            gemini_config["thinkingConfig"] = thinking_config

        # Обработка инструментов (Tools)
        tools = data.get('tools', [])
        gemini_tools = []
        if tools:
            declarations = []
            for tool in tools:
                if tool.get('type') == 'function':
                    func = tool.get('function', {})
                    declarations.append({
                        "name": func.get('name'),
                        "description": func.get('description'),
                        "parameters": clean_gemini_schema(func.get('parameters'))
                    })
            if declarations:
                gemini_tools = [{"function_declarations": declarations}]

        # Определение режима работы (Quota vs Vertex)
        is_quota_mode = 'quota' in raw_model
        
        # --- Подготовка запроса ---
        url = ""
        headers = {}
        payload = {}
        params = {}

        if is_quota_mode:
            # --- Gemini CLI / Cloud Code Emulation Mode ---
            with auth_lock:
                if not user_creds:
                    return create_openai_error("Authentication not initialized. Please run auth script.", "auth_error", 401), 401
                token = user_creds.token
            
            project_id = discover_project_id(token)
            if not project_id:
                return create_openai_error("Google Cloud Project ID not found. Set GOOGLE_CLOUD_PROJECT env var.", "config_error", 500), 500

            # Cloud Code API Payload
            payload = {
                "model": target_model,
                "project": project_id,
                "request": {
                    "contents": contents,
                    "generationConfig": gemini_config
                }
            }

            if gemini_tools:
                payload["request"]["tools"] = gemini_tools
            
            # System instruction workaround for Cloud Code
            if system_instruction:
                 # Пытаемся использовать нативную поддержку, если она есть в API
                 # Если нет, используем более чистый prepend
                 payload["request"]["system_instruction"] = {"parts": [{"text": system_instruction}]}

            url = f"{CLOUD_CODE_ENDPOINT}:{'streamGenerateContent' if stream else 'generateContent'}"
            if stream: params = {"alt": "sse"}
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            # Note: We explicitly DO NOT set x-goog-user-project here for Quota mode.
            # The quota should be billed to the Gemini CLI project (via Client ID),
            # not the user's project. Setting this header forces a check for the
            # Cloud Code API in the user's project, which fails if not enabled.

        else:
            # --- Standard Vertex AI Mode ---
            project_id = os.environ.get('VERTEX_PROJECT_ID')
            location = os.environ.get('VERTEX_LOCATION', 'us-central1')
            token = get_vertex_token()
            
            if not token:
                 return create_openai_error("Vertex AI Service Account not found.", "auth_error", 500), 500

            payload = {
                "contents": contents,
                "generationConfig": gemini_config
            }

            if gemini_tools:
                payload["tools"] = gemini_tools
            
            if system_instruction:
                payload["system_instruction"] = {"parts": [{"text": system_instruction}]}

            url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{target_model}:{'streamGenerateContent' if stream else 'generateContent'}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "x-goog-user-project": project_id
            }

        # --- Выполнение запроса ---
        
        if stream:
            def generate_stream():
                client = httpx.Client(timeout=60.0)
                usage_accumulated = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                
                try:
                    with client.stream("POST", url, headers=headers, json=payload, params=params) as r:
                        if r.status_code != 200:
                            err_text = r.read().decode()
                            print(f"[ERROR] Stream API Error {r.status_code}: {err_text}", flush=True)
                            yield f"data: {create_openai_error(f'Upstream API Error: {err_text}', 'upstream_error', r.status_code)}\n\n"
                            return

                        for line in r.iter_lines():
                            if not line: continue
                            
                            # Обработка SSE от Cloud Code (data: json) или Vertex (json массив)
                            chunk_data = None
                            
                            if is_quota_mode:
                                if line.startswith("data: "):
                                    data_str = line[6:].strip()
                                    if data_str == "[DONE]": break
                                    try:
                                        chunk_data = json.loads(data_str)
                                        # Unwrap Cloud Code response wrapper
                                        chunk_data = chunk_data.get("response", chunk_data)
                                    except: continue
                            else:
                                # Vertex возвращает JSON объекты в массиве, иногда с запятыми
                                clean_line = line.strip().strip(',').strip('[').strip(']')
                                try:
                                    chunk_data = json.loads(clean_line)
                                except: continue

                            if not chunk_data: continue

                            # Извлечение кандидатов и текста
                            candidates = chunk_data.get('candidates', [])
                            if candidates:
                                candidate = candidates[0]
                                
                                # Обработка Safety Filters и других причин завершения
                                finish_reason = candidate.get('finishReason')
                                if finish_reason and finish_reason in ["SAFETY", "RECITATION", "OTHER"]:
                                    error_msg = f"Gemini stream interrupted by safety filters or other reason: {finish_reason}"
                                    yield f"data: {create_openai_error(error_msg, 'policy_violation', 400)}\n\n"
                                    return

                                content = candidate.get('content', {})
                                parts = content.get('parts', [])
                                
                                if not parts:
                                    continue
                                    
                                function_call = None
                                for part in parts:
                                    text = part.get('text', '')
                                    # В Gemini API 'thought' обычно флаг, а текст мысли в 'text'
                                    # Но иногда может прийти и как объект/строка в самом 'thought'
                                    thought_val = part.get('thought')
                                    is_thought = thought_val is not None
                                    
                                    if is_thought:
                                        # Извлекаем текст мысли: приоритет полю 'text', если оно пустое - пробуем 'thought'
                                        thought_text = text if text else (thought_val if isinstance(thought_val, str) else "")
                                        if thought_text:
                                            openai_chunk = {
                                                "id": f"chatcmpl-{int(time.time())}",
                                                "object": "chat.completion.chunk",
                                                "created": int(time.time()),
                                                "model": raw_model,
                                                "choices": [{
                                                    "index": 0,
                                                    "delta": {"reasoning_content": thought_text},
                                                    "finish_reason": None
                                                }]
                                            }
                                            yield f"data: {json.dumps(openai_chunk, ensure_ascii=False)}\n\n"
                                        continue

                                    if text:
                                        # OpenAI Stream Chunk Format
                                        openai_chunk = {
                                            "id": f"chatcmpl-{int(time.time())}",
                                            "object": "chat.completion.chunk",
                                            "created": int(time.time()),
                                            "model": raw_model,
                                            "choices": [{
                                                "index": 0,
                                                "delta": {"content": text},
                                                "finish_reason": None
                                            }]
                                        }
                                        yield f"data: {json.dumps(openai_chunk, ensure_ascii=False)}\n\n"
                                    
                                    if part.get('functionCall'):
                                        function_call = part.get('functionCall')
                                
                                if function_call:
                                    tool_call_id = f"call_{int(time.time())}"
                                    openai_chunk = {
                                        "id": f"chatcmpl-{int(time.time())}",
                                        "object": "chat.completion.chunk",
                                        "created": int(time.time()),
                                        "model": raw_model,
                                        "choices": [{
                                            "index": 0,
                                            "delta": {
                                                "tool_calls": [{
                                                    "index": 0,
                                                    "id": tool_call_id,
                                                    "type": "function",
                                                    "function": {
                                                        "name": function_call.get('name'),
                                                        "arguments": json.dumps(function_call.get('args', {}))
                                                    }
                                                }]
                                            },
                                            "finish_reason": None
                                        }]
                                    }
                                    yield f"data: {json.dumps(openai_chunk, ensure_ascii=False)}\n\n"

                            # Сбор статистики использования (если доступна в чанке)
                            usage_meta = chunk_data.get('usageMetadata', {})
                            if usage_meta:
                                usage_accumulated["prompt_tokens"] = usage_meta.get('promptTokenCount', 0)
                                usage_accumulated["completion_tokens"] = usage_meta.get('candidatesTokenCount', 0)
                                usage_accumulated["total_tokens"] = usage_meta.get('totalTokenCount', 0)
                                if 'thoughtsTokenCount' in usage_meta:
                                    if "completion_tokens_details" not in usage_accumulated:
                                        usage_accumulated["completion_tokens_details"] = {}
                                    usage_accumulated["completion_tokens_details"]["reasoning_tokens"] = usage_meta['thoughtsTokenCount']

                    # Финальный чанк с usage (для Kilo Code)
                    if include_usage:
                        usage_chunk = {
                            "id": f"chatcmpl-{int(time.time())}",
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": raw_model,
                            "choices": [],
                            "usage": usage_accumulated
                        }
                        yield f"data: {json.dumps(usage_chunk, ensure_ascii=False)}\n\n"
                    
                    yield "data: [DONE]\n\n"

                except Exception as e:
                    print(f"[ERROR] Stream Exception: {e}", flush=True)
                    yield f"data: {create_openai_error(str(e), 'stream_exception')}\n\n"
                finally:
                    client.close()

            return Response(stream_with_context(generate_stream()), mimetype='text/event-stream')

        else:
            # Non-streaming request
            with httpx.Client(timeout=60.0) as client:
                r = client.post(url, headers=headers, json=payload)
                
                if r.status_code != 200:
                    print(f"[ERROR] API Error {r.status_code}: {r.text}", flush=True)
                    return create_openai_error(f"Upstream Error: {r.text}", "upstream_error", r.status_code), r.status_code
                
                resp_data = r.json()
                if is_quota_mode:
                    resp_data = resp_data.get("response", resp_data)
                
                candidates = resp_data.get('candidates', [])
                text = ""
                reasoning_text = ""
                function_call = None
                finish_reason = "stop"
                
                if candidates:
                    candidate = candidates[0]
                    gemini_finish = candidate.get('finishReason')
                    
                    if gemini_finish in ["SAFETY", "RECITATION", "OTHER"]:
                        return create_openai_error(f"Gemini blocked request: {gemini_finish}", "policy_violation", 400), 400

                    content = candidate.get('content', {})
                    parts = content.get('parts', [])
                    
                    for part in parts:
                        p_text = part.get('text', '')
                        thought = part.get('thought')
                        if thought is True or 'thought' in part:
                            reasoning_text += p_text if isinstance(thought, bool) else part.get('thought', '')
                        else:
                            text += p_text
                            if not function_call:
                                function_call = part.get('functionCall')
                    
                    # Map Gemini finishReason to OpenAI
                    if gemini_finish == "MAX_TOKENS": finish_reason = "length"
                    elif function_call: finish_reason = "tool_calls"
                    # else default to stop

                usage = resp_data.get('usageMetadata', {})
                
                message_content = {
                    "role": "assistant",
                    "content": text
                }
                if reasoning_text:
                    message_content["reasoning_content"] = reasoning_text
                
                if function_call:
                    message_content["tool_calls"] = [{
                        "id": f"call_{int(time.time())}",
                        "type": "function",
                        "function": {
                            "name": function_call.get('name'),
                            "arguments": json.dumps(function_call.get('args', {}))
                        }
                    }]
                
                openai_response = {
                    "id": f"chatcmpl-{int(time.time())}",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": raw_model,
                    "choices": [{
                        "index": 0,
                        "message": message_content,
                        "finish_reason": finish_reason
                    }],
                    "usage": {
                        "prompt_tokens": usage.get('promptTokenCount', 0),
                        "completion_tokens": usage.get('candidatesTokenCount', 0),
                        "total_tokens": usage.get('totalTokenCount', 0)
                    }
                }
                
                if 'thoughtsTokenCount' in usage:
                    openai_response["usage"]["completion_tokens_details"] = {
                        "reasoning_tokens": usage['thoughtsTokenCount']
                    }
                
                return json.dumps(openai_response, ensure_ascii=False), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return create_openai_error(f"Internal Proxy Error: {str(e)}", "internal_error", 500), 500

@app.route('/v1/models', methods=['GET'])
def list_models():
    models = [
        "gemini-3-pro-preview-quota", "gemini-3-flash-preview-quota",
        "gemini-2.5-pro-quota", "gemini-2.5-flash-quota", "gemini-2.5-flash-lite-quota",
        "gemini-3-pro-preview-vertex", "gemini-3-flash-preview-vertex",
        "gemini-2.5-pro-vertex", "gemini-2.5-flash-vertex", "gemini-2.5-flash-lite-vertex",
        "gemini-3-pro-image-vertex", "gemini-2.5-flash-image-vertex",
        "nano-banana"
    ]
    return json.dumps({"data": [{"id": m, "object": "model"} for m in models]})

if __name__ == "__main__":
    threading.Thread(target=refresh_user_creds, daemon=True).start()
    app.run(host='0.0.0.0', port=4000, debug=False)

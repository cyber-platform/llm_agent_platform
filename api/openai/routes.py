import os
import json
import time
import httpx
from flask import Blueprint, request, Response, stream_with_context
from config import CLOUD_CODE_ENDPOINT
from auth.credentials import get_user_creds, get_auth_lock, get_vertex_token
from auth.discovery import discover_project_id
from core.models import map_model_name
from core.utils import sanitize_data, sanitize_string, clean_gemini_schema, create_openai_error
from api.openai.transform import transform_openai_to_gemini

openai_bp = Blueprint('openai', __name__)

@openai_bp.route('/v1/chat/completions', methods=['POST'])
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
        
        # Sanitize inputs to prevent UTF-8 encoding errors with surrogates
        contents = sanitize_data(contents)
        if system_instruction:
            system_instruction = sanitize_string(system_instruction)

        # Базовая конфигурация для Gemini
        max_tokens = data.get('max_tokens')
        if max_tokens is None or max_tokens == -1:
            # Согласно документации Gemini 2.5/3.0 Pro/Flash, лимит вывода составляет 65,536 токенов.
            # Устанавливаем этот максимум, если в Kilo Code выбрано -1 (без ограничений).
            max_tokens = 65535
        
        gemini_config = {
            "temperature": data.get('temperature', 0.7),
            "maxOutputTokens": int(max_tokens),
            "topP": data.get('top_p', 1.0),
            "topK": data.get('top_k', 40),
        }

        stop_sequences = data.get('stop')
        if stop_sequences:
            if isinstance(stop_sequences, str):
                gemini_config["stopSequences"] = [stop_sequences]
            elif isinstance(stop_sequences, list):
                gemini_config["stopSequences"] = stop_sequences

        # Поддержка reasoning (thinking)
        reasoning_effort = data.get('reasoning_effort')
        max_thinking_tokens = data.get('modelMaxThinkingTokens') or data.get('max_completion_tokens')
        
        if reasoning_effort or max_thinking_tokens or data.get('enableReasoningEffort'):
            thinking_config = {
                "includeThoughts": True
            }
            if max_thinking_tokens:
                thinking_config["thinkingBudget"] = int(max_thinking_tokens)
            
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
            user_creds = get_user_creds()
            auth_lock = get_auth_lock()
            print(f"[DEBUG] Before auth_lock: user_creds={user_creds}", flush=True)
            with auth_lock:
                print(f"[DEBUG] Inside auth_lock: user_creds={user_creds}", flush=True)
                # Check if credentials are available (should be after initialization)
                if not user_creds or not hasattr(user_creds, 'token') or not user_creds.token:
                    print(f"[DEBUG] Auth check failed: user_creds={user_creds}, hasattr={hasattr(user_creds, 'token') if user_creds else 'N/A'}, token={getattr(user_creds, 'token', None) if user_creds else 'N/A'}", flush=True)
                    return create_openai_error("Authentication not initialized. Please run auth script.", "auth_error", 401), 401
                token = user_creds.token
            print(f"[DEBUG] After auth_lock: token={token[:30] if token else None}...", flush=True)
            
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
                                gemini_finish = candidate.get('finishReason')
                                openai_finish = None
                                if gemini_finish:
                                    if gemini_finish == "STOP": openai_finish = "stop"
                                    elif gemini_finish == "MAX_TOKENS": openai_finish = "length"
                                    elif gemini_finish in ["SAFETY", "RECITATION", "OTHER"]:
                                        error_msg = f"Gemini stream interrupted by safety filters or other reason: {gemini_finish}"
                                        yield f"data: {create_openai_error(error_msg, 'policy_violation', 400)}\n\n"
                                        return

                                content = candidate.get('content', {})
                                parts = content.get('parts', [])
                                
                                if not parts:
                                    continue
                                    
                                current_tool_calls = []
                                for part in parts:
                                    text = part.get('text', '')
                                    thought_val = part.get('thought')
                                    is_thought = thought_val is not None
                                    
                                    if is_thought:
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
                                                    "finish_reason": openai_finish
                                                }]
                                            }
                                            yield f"data: {json.dumps(sanitize_data(openai_chunk), ensure_ascii=False)}\n\n"
                                        continue

                                    if text:
                                        openai_chunk = {
                                            "id": f"chatcmpl-{int(time.time())}",
                                            "object": "chat.completion.chunk",
                                            "created": int(time.time()),
                                            "model": raw_model,
                                            "choices": [{
                                                "index": 0,
                                                "delta": {"content": text},
                                                "finish_reason": openai_finish
                                            }]
                                        }
                                        yield f"data: {json.dumps(sanitize_data(openai_chunk), ensure_ascii=False)}\n\n"
                                    
                                    if part.get('functionCall'):
                                        current_tool_calls.append(part.get('functionCall'))
                                
                                if current_tool_calls:
                                    openai_tool_calls = []
                                    for idx, fn in enumerate(current_tool_calls):
                                        openai_tool_calls.append({
                                            "index": idx,
                                            "id": fn.get('id') or f"call_{int(time.time())}_{idx}",
                                            "type": "function",
                                            "function": {
                                                "name": fn.get('name'),
                                                "arguments": json.dumps(fn.get('args', {}))
                                            }
                                        })
                                    
                                    openai_chunk = {
                                        "id": f"chatcmpl-{int(time.time())}",
                                        "object": "chat.completion.chunk",
                                        "created": int(time.time()),
                                        "model": raw_model,
                                        "choices": [{
                                            "index": 0,
                                            "delta": {"tool_calls": openai_tool_calls},
                                            "finish_reason": openai_finish or ("tool_calls" if current_tool_calls else None)
                                        }]
                                    }
                                    yield f"data: {json.dumps(sanitize_data(openai_chunk), ensure_ascii=False)}\n\n"

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
                        yield f"data: {json.dumps(sanitize_data(usage_chunk), ensure_ascii=False)}\n\n"
                    
                    yield "data: [DONE]\n\n"

                except Exception as e:
                    print(f"[ERROR] Stream Exception: {e}", flush=True)
                    yield f"data: {create_openai_error(str(e), 'stream_exception')}\n\n"
                finally:
                    client.close()

            return Response(stream_with_context(generate_stream()), mimetype='text/event-stream')

        else:
            # Non-streaming request with fallback logic
            fallback_chain = [target_model]
            if 'gemini-3-flash' in target_model:
                fallback_chain.extend(['gemini-2.5-flash', 'gemini-2.5-flash-lite'])
            elif 'gemini-3.1-pro' in target_model:
                fallback_chain.append('gemini-2.5-pro')

            last_r = None
            for current_model in fallback_chain:
                # Update payload/URL for the current attempt
                attempt_payload = payload.copy()
                attempt_url = url
                
                if is_quota_mode:
                    attempt_payload["model"] = current_model
                else:
                    # Rebuild Vertex URL for the specific fallback model
                    location = os.environ.get('VERTEX_LOCATION', 'us-central1')
                    project_id = os.environ.get('VERTEX_PROJECT_ID')
                    attempt_url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{current_model}:generateContent"

                with httpx.Client(timeout=60.0) as client:
                    r = client.post(attempt_url, headers=headers, json=attempt_payload)
                    last_r = r
                    
                    if r.status_code == 429 and "capacity" in r.text.lower():
                        print(f"[WARN] Model {current_model} exhausted (capacity). Trying fallback...", flush=True)
                        continue
                    
                    if r.status_code != 200:
                        print(f"[ERROR] API Error {r.status_code}: {r.text}", flush=True)
                        return create_openai_error(f"Upstream Error: {r.text}", "upstream_error", r.status_code), r.status_code
                    
                    resp_data = r.json()
                    break # Success!
            else:
                # If all fallbacks failed
                return create_openai_error(f"Upstream Error (All fallbacks exhausted): {last_r.text}", "upstream_error", r.status_code), last_r.status_code
            
            if is_quota_mode:
                resp_data = resp_data.get("response", resp_data)
                
                candidates = resp_data.get('candidates', [])
                text = ""
                reasoning_text = ""
                all_function_calls = []
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
                        if thought is not None:
                            reasoning_text += p_text if p_text else (thought if isinstance(thought, str) else "")
                        else:
                            if p_text:
                                text += p_text
                            if part.get('functionCall'):
                                all_function_calls.append(part.get('functionCall'))
                    
                    # Map Gemini finishReason to OpenAI
                    if gemini_finish == "MAX_TOKENS": finish_reason = "length"
                    elif all_function_calls: finish_reason = "tool_calls"
                    # else default to stop
                
                usage = resp_data.get('usageMetadata', {})
                
                message_content = {
                    "role": "assistant",
                    "content": text
                }
                if reasoning_text:
                    message_content["reasoning_content"] = reasoning_text
                
                if all_function_calls:
                    message_content["tool_calls"] = []
                    for idx, fn in enumerate(all_function_calls):
                        message_content["tool_calls"].append({
                            "id": fn.get('id') or f"call_{int(time.time())}_{idx}",
                            "type": "function",
                            "function": {
                                "name": fn.get('name'),
                                "arguments": json.dumps(fn.get('args', {}))
                            }
                        })
                
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
                
                return json.dumps(sanitize_data(openai_response), ensure_ascii=False), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return create_openai_error(f"Internal Proxy Error: {str(e)}", "internal_error", 500), 500

@openai_bp.route('/v1/models', methods=['GET'])
def list_models():
    models = [
        "gemini-3.1-pro-preview-quota",
        "gemini-3-flash-preview-quota",
        "gemini-2.5-pro-quota", "gemini-2.5-flash-quota", "gemini-2.5-flash-lite-quota",
        "gemini-3.1-pro-preview-vertex", "gemini-3-flash-preview-vertex",
        "gemini-2.5-pro-vertex", "gemini-2.5-flash-vertex", "gemini-2.5-flash-lite-vertex",
        "gemini-3-pro-image-vertex", "gemini-2.5-flash-image-vertex",
        "nano-banana"
    ]
    return json.dumps({"data": [{"id": m, "object": "model"} for m in models]})

import os
import json
import time
from flask import Blueprint, request, Response, stream_with_context
from config import CLOUD_CODE_ENDPOINT, DEFAULT_QUOTA_MODEL, STRICT_CLI_PARITY
from auth.credentials import (
    get_auth_availability,
    get_auth_lock,
    get_gemini_access_token_from_file,
    get_user_creds,
    get_vertex_token,
)
from auth.qwen_oauth import (
    refresh_qwen_credentials_file,
)
from core.models import map_model_name
from core.utils import sanitize_data, sanitize_string, clean_gemini_schema, create_openai_error
from api.openai.transform import transform_openai_to_gemini
from services.http_pool import get_http_client
from services.account_router import (
    AllAccountsExhaustedError,
    GeminiAccount,
    quota_account_router,
)
from services.quota_transport import (
    build_quota_payload,
    generate_session_id,
    generate_user_prompt_id,
    is_quota_limit_response,
    parse_cloud_code_sse_line,
    send_generate,
    send_generate_to_url,
    stream_generate_lines,
    stream_generate_lines_from_url,
    unwrap_cloud_code_response,
)

openai_bp = Blueprint('openai', __name__)


def _is_qwen_quota_model(raw_model: str) -> bool:
    return 'qwen' in raw_model and 'quota' in raw_model


def _is_gemini_quota_model(raw_model: str) -> bool:
    return 'quota' in raw_model and not _is_qwen_quota_model(raw_model)


def _qwen_completion_url(resource_url: str) -> str:
    normalized = resource_url.strip()
    if not normalized.startswith('http://') and not normalized.startswith('https://'):
        normalized = f'https://{normalized}'
    if normalized.endswith('/'):
        normalized = normalized[:-1]
    if not normalized.endswith('/v1'):
        normalized = f'{normalized}/v1'
    return f'{normalized}/chat/completions'


def _qwen_payload_from_openai(data: dict, target_model: str) -> dict:
    payload = {
        "model": target_model,
        "messages": data.get('messages', []),
        "stream": bool(data.get('stream', False)),
    }

    for field in [
        'temperature',
        'top_p',
        'max_tokens',
        'max_completion_tokens',
        'presence_penalty',
        'frequency_penalty',
        'stop',
        'tools',
        'tool_choice',
        'response_format',
        'stream_options',
    ]:
        if field in data:
            payload[field] = data[field]

    return payload


def _stream_quota_error(error_payload: str):
    yield f"data: {error_payload}\n\n"
    yield "data: [DONE]\n\n"


def _openai_chunk_from_qwen(parsed: dict, raw_model: str) -> dict:
    choice = (parsed.get("choices") or [{}])[0]
    delta = choice.get("delta", {})

    if not delta and "message" in choice:
        msg = choice.get("message", {})
        delta = {
            "role": msg.get("role", "assistant"),
            "content": msg.get("content", ""),
        }

    return {
        "id": parsed.get("id", f"chatcmpl-{int(time.time())}"),
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": raw_model,
        "choices": [{
            "index": choice.get("index", 0),
            "delta": delta,
            "finish_reason": choice.get("finish_reason"),
        }],
    }

@openai_bp.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    try:
        data = request.json
        if not isinstance(data, dict):
            data = {}
        raw_model = data.get('model', DEFAULT_QUOTA_MODEL)
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
        max_completion_tokens = data.get('max_completion_tokens')
        max_tokens = max_completion_tokens if max_completion_tokens is not None else data.get('max_tokens')
        
        gemini_config = {
            "temperature": data.get('temperature', 0.7),
            "topP": data.get('top_p', 1.0),
            "topK": data.get('top_k', 40),
        }

        if max_tokens is not None and max_tokens != -1:
            gemini_config["maxOutputTokens"] = int(max_tokens)

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
        is_qwen_quota_mode = _is_qwen_quota_model(raw_model)
        is_gemini_quota_mode = _is_gemini_quota_model(raw_model)
        is_quota_mode = is_qwen_quota_mode or is_gemini_quota_mode
        
        # --- Подготовка запроса ---
        url = ""
        headers = {}
        payload = {}
        params = {}
        selected_account = None
        token = None
        quota_request_payload = None
        session_id = None
        user_prompt_id = None

        if is_qwen_quota_mode:
            try:
                selected_account = quota_account_router.select_account("qwen")
            except AllAccountsExhaustedError:
                return create_openai_error(
                    "all_accounts_exceed_quota",
                    "quota_exhausted",
                    429,
                ), 429

            account = selected_account.account
            try:
                qwen_creds = refresh_qwen_credentials_file(account.credentials_path)
            except Exception as e:
                return create_openai_error(f"Qwen OAuth refresh failed: {e}", "auth_error", 401), 401
            token = qwen_creds.get("access_token")
            resource_url = qwen_creds.get("resource_url")
            if not token or not resource_url:
                return create_openai_error(
                    "Qwen OAuth credentials must include access_token and resource_url",
                    "auth_error",
                    401,
                ), 401

            payload = _qwen_payload_from_openai(data, target_model)
            url = _qwen_completion_url(resource_url)
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
        elif is_gemini_quota_mode:
            try:
                selected_account = quota_account_router.select_account("gemini")
            except AllAccountsExhaustedError:
                return create_openai_error(
                    "all_accounts_exceed_quota",
                    "quota_exhausted",
                    429,
                ), 429

            account = selected_account.account
            if not isinstance(account, GeminiAccount):
                return create_openai_error(
                    "Invalid Gemini account configuration",
                    "config_error",
                    500,
                ), 500

            auth_lock = get_auth_lock()
            with auth_lock:
                token = get_gemini_access_token_from_file(account.credentials_path)

            session_id = data.get("session_id") or request.headers.get("x-session-id") or generate_session_id()
            user_prompt_id = data.get("user_prompt_id") or request.headers.get("x-user-prompt-id") or generate_user_prompt_id()

            quota_request_payload = {
                "contents": contents,
                "generationConfig": gemini_config,
            }

            if gemini_tools:
                quota_request_payload["tools"] = gemini_tools

            if system_instruction:
                quota_request_payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

            payload = build_quota_payload(
                model=target_model,
                project=account.project_id,
                request_payload=quota_request_payload,
                user_prompt_id=user_prompt_id,
                session_id=session_id,
            )

            url = f"{CLOUD_CODE_ENDPOINT}:{'streamGenerateContent' if stream else 'generateContent'}"
            if stream:
                params = {"alt": "sse"}
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }

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
                usage_accumulated = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                
                try:
                    if is_quota_mode:
                        if is_qwen_quota_mode:
                            lines = stream_generate_lines_from_url(
                                token,
                                payload,
                                url,
                                params=None,
                            )
                        else:
                            lines = stream_generate_lines(token, payload)
                    else:
                        client = get_http_client()
                        response = client.stream("POST", url, headers=headers, json=payload, params=params)
                        lines = None

                    if not is_quota_mode:
                        with response as r:
                            if r.status_code != 200:
                                err_text = r.read().decode()
                                print(f"[ERROR] Stream API Error {r.status_code}: {err_text}", flush=True)
                                yield f"data: {create_openai_error(f'Upstream API Error: {err_text}', 'upstream_error', r.status_code)}\n\n"
                                return

                            for line in r.iter_lines():
                                if not line:
                                    continue

                                clean_line = line.strip().strip(',').strip('[').strip(']')
                                try:
                                    chunk_data = json.loads(clean_line)
                                except Exception:
                                    continue

                                if not chunk_data:
                                    continue

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
                    else:
                        for line in lines:
                            if is_qwen_quota_mode and line.startswith("data: "):
                                raw = line[6:].strip()
                                if raw == "[DONE]":
                                    quota_account_router.register_success("qwen", selected_account.account.name)
                                    break
                                try:
                                    parsed = json.loads(raw)
                                except Exception:
                                    continue

                                if isinstance(parsed, dict) and parsed.get("error"):
                                    error_text = json.dumps(parsed.get("error"), ensure_ascii=False)
                                    if selected_account.mode == "rounding":
                                        switched = quota_account_router.register_quota_limit(
                                            "qwen",
                                            selected_account.account.name,
                                            selected_account.mode,
                                            selected_account.pool,
                                        )
                                        if switched and quota_account_router.all_accounts_exhausted("qwen", selected_account.pool):
                                            yield f"data: {create_openai_error('all_accounts_exceed_quota', 'quota_exhausted', 429)}\n\n"
                                            return

                                    yield f"data: {create_openai_error(f'Upstream API Error: {error_text}', 'upstream_error', 429)}\n\n"
                                    return

                                openai_chunk = _openai_chunk_from_qwen(parsed, raw_model)
                                yield f"data: {json.dumps(sanitize_data(openai_chunk), ensure_ascii=False)}\n\n"

                                usage = parsed.get("usage")
                                if usage:
                                    usage_accumulated["prompt_tokens"] = usage.get("prompt_tokens", 0)
                                    usage_accumulated["completion_tokens"] = usage.get("completion_tokens", 0)
                                    usage_accumulated["total_tokens"] = usage.get("total_tokens", 0)
                                continue

                            chunk_data = parse_cloud_code_sse_line(line)
                            if not chunk_data:
                                continue
                            if chunk_data.get("done"):
                                break

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

                    if is_gemini_quota_mode and selected_account is not None:
                        quota_account_router.register_success("gemini", selected_account.account.name)
                    
                    yield "data: [DONE]\n\n"

                except Exception as e:
                    if is_quota_mode and selected_account is not None:
                        error_text = str(e)
                        if error_text.startswith("429:"):
                            provider = "qwen" if is_qwen_quota_mode else "gemini"
                            switched = quota_account_router.register_quota_limit(
                                provider,
                                selected_account.account.name,
                                selected_account.mode,
                                selected_account.pool,
                            )
                            if switched and quota_account_router.all_accounts_exhausted(provider, selected_account.pool):
                                yield from _stream_quota_error(
                                    create_openai_error("all_accounts_exceed_quota", "quota_exhausted", 429)
                                )
                                return

                    print(f"[ERROR] Stream Exception: {e}", flush=True)
                    yield f"data: {create_openai_error(str(e), 'stream_exception')}\n\n"

            return Response(stream_with_context(generate_stream()), mimetype='text/event-stream')

        else:
            # Non-streaming request with fallback logic
            fallback_chain = [target_model]
            if not (is_quota_mode and STRICT_CLI_PARITY) and 'gemini-3-flash' in target_model:
                fallback_chain.extend(['gemini-2.5-flash', 'gemini-2.5-flash-lite'])
            elif not (is_quota_mode and STRICT_CLI_PARITY) and 'gemini-3.1-pro' in target_model:
                fallback_chain.append('gemini-2.5-pro')

            last_r = None
            resp_data = None
            max_attempts = len(fallback_chain)
            if is_quota_mode and selected_account is not None and selected_account.mode == "rounding":
                max_attempts = max(max_attempts, len(selected_account.pool))

            attempt = 0
            while attempt < max_attempts:
                current_model = fallback_chain[min(attempt, len(fallback_chain) - 1)]
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

                if is_quota_mode:
                    if is_qwen_quota_mode:
                        r = send_generate_to_url(
                            token,
                            attempt_payload,
                            attempt_url,
                        )
                    else:
                        r = send_generate(token, attempt_payload)
                else:
                    client = get_http_client()
                    r = client.post(attempt_url, headers=headers, json=attempt_payload)
                last_r = r

                if is_quota_mode and selected_account is not None and is_quota_limit_response(r.status_code, r.text):
                    provider = "qwen" if is_qwen_quota_mode else "gemini"
                    switched = quota_account_router.register_quota_limit(
                        provider,
                        selected_account.account.name,
                        selected_account.mode,
                        selected_account.pool,
                    )
                    if switched and quota_account_router.all_accounts_exhausted(provider, selected_account.pool):
                        return create_openai_error("all_accounts_exceed_quota", "quota_exhausted", 429), 429

                    if switched and selected_account.mode == "rounding":
                        selected_account = quota_account_router.select_account(provider)
                        if provider == "gemini":
                            account = selected_account.account
                            if not isinstance(account, GeminiAccount):
                                return create_openai_error("Invalid Gemini account configuration", "config_error", 500), 500
                            with get_auth_lock():
                                token = get_gemini_access_token_from_file(account.credentials_path)
                            payload = build_quota_payload(
                                model=current_model,
                                project=account.project_id,
                                request_payload=quota_request_payload or {},
                                user_prompt_id=user_prompt_id or generate_user_prompt_id(),
                                session_id=session_id,
                            )
                        else:
                            try:
                                qwen_creds = refresh_qwen_credentials_file(selected_account.account.credentials_path)
                            except Exception as e:
                                return create_openai_error(f"Qwen OAuth refresh failed: {e}", "auth_error", 401), 401
                            token = qwen_creds.get("access_token")
                            resource_url = qwen_creds.get("resource_url")
                            if not token or not resource_url:
                                return create_openai_error(
                                    "Qwen OAuth credentials must include access_token and resource_url",
                                    "auth_error",
                                    401,
                                ), 401
                            url = _qwen_completion_url(resource_url)
                        attempt += 1
                        continue

                if r.status_code == 429 and "capacity" in r.text.lower() and len(fallback_chain) > 1 and not is_quota_mode:
                    print(f"[WARN] Model {current_model} exhausted (capacity). Trying fallback...", flush=True)
                    attempt += 1
                    continue

                if r.status_code != 200:
                    print(f"[ERROR] API Error {r.status_code}: {r.text}", flush=True)
                    return create_openai_error(f"Upstream Error: {r.text}", "upstream_error", r.status_code), r.status_code

                try:
                    resp_data = r.json()
                except Exception:
                    return create_openai_error(f"Upstream Error: {r.text}", "upstream_error", 502), 502

                if is_quota_mode and selected_account is not None:
                    provider = "qwen" if is_qwen_quota_mode else "gemini"
                    quota_account_router.register_success(provider, selected_account.account.name)
                break # Success!

            else:
                # If all fallbacks failed
                if last_r is None:
                    return create_openai_error("Upstream Error (No attempts executed)", "upstream_error", 500), 500
                return create_openai_error(f"Upstream Error (All fallbacks exhausted): {last_r.text}", "upstream_error", last_r.status_code), last_r.status_code
            
            if is_gemini_quota_mode:
                resp_data = unwrap_cloud_code_response(resp_data)

            if is_qwen_quota_mode:
                if isinstance(resp_data, dict):
                    resp_data["model"] = raw_model
                return json.dumps(sanitize_data(resp_data), ensure_ascii=False), 200

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
    availability = get_auth_availability()

    models = []
    if availability.gemini_quota:
        models.extend([
            "gemini-3.1-pro-preview-quota",
            "gemini-3-flash-preview-quota",
            "gemini-2.5-pro-quota",
            "gemini-2.5-flash-quota",
            "gemini-2.5-flash-lite-quota",
        ])

    if availability.qwen_quota:
        models.append("qwen-coder-model-quota")

    if availability.vertex:
        models.extend([
            "gemini-3.1-pro-preview-vertex",
            "gemini-3-flash-preview-vertex",
            "gemini-2.5-pro-vertex",
            "gemini-2.5-flash-vertex",
            "gemini-2.5-flash-lite-vertex",
            "gemini-3-pro-image-vertex",
            "gemini-2.5-flash-image-vertex",
            "nano-banana",
        ])

    return json.dumps({"data": [{"id": m, "object": "model"} for m in models]})

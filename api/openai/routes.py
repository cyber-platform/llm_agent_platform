import os
import json
import time
from dataclasses import dataclass
from flask import Blueprint, request, Response, stream_with_context
from config import CLOUD_CODE_ENDPOINT, DEFAULT_QUOTA_MODEL, STRICT_CLI_PARITY
from core.logging import get_logger
from auth.credentials import (
    get_auth_availability,
    get_auth_lock,
    get_gemini_access_token_from_file,
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
    AccountRouterError,
    GeminiAccount,
    RotationEvent,
    SelectedAccount,
    quota_account_router,
)
from services.quota_transport import (
    build_quota_payload,
    classify_429_error_payload,
    classify_429_exception,
    classify_429_response,
    generate_session_id,
    generate_user_prompt_id,
    Quota429Type,
    parse_cloud_code_sse_line,
    send_generate,
    send_generate_to_url,
    stream_generate_lines,
    stream_generate_lines_from_url,
    unwrap_cloud_code_response,
)

openai_bp = Blueprint('openai', __name__)
logger = get_logger(__name__)


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


@dataclass
class StreamRuntimeState:
    token: str | None
    payload: dict
    url: str
    selected_account: SelectedAccount | None


@dataclass
class ChatRequestContext:
    data: dict
    raw_model: str
    target_model: str
    messages: list
    stream: bool
    include_usage: bool
    contents: list
    system_instruction: str | None
    gemini_config: dict
    gemini_tools: list
    is_qwen_quota_mode: bool
    is_gemini_quota_mode: bool
    is_quota_mode: bool


@dataclass
class UpstreamRequestContext:
    token: str | None
    payload: dict
    url: str
    headers: dict
    params: dict
    selected_account: SelectedAccount | None
    quota_request_payload: dict | None
    session_id: str | None
    user_prompt_id: str | None


class UpstreamPreparationError(Exception):
    def __init__(self, message: str, error_type: str, status_code: int):
        super().__init__(message)
        self.message = message
        self.error_type = error_type
        self.status_code = status_code


def _map_gemini_finish_reason(gemini_finish: str | None) -> str | None:
    if gemini_finish == "STOP":
        return "stop"
    if gemini_finish == "MAX_TOKENS":
        return "length"
    return None


def _build_openai_stream_chunk(raw_model: str, delta: dict, finish_reason: str | None, index: int = 0) -> dict:
    return {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": raw_model,
        "choices": [{
            "index": index,
            "delta": delta,
            "finish_reason": finish_reason,
        }],
    }


def _convert_gemini_stream_chunk(chunk_data: dict, raw_model: str) -> tuple[list[dict], str | None]:
    candidates = chunk_data.get('candidates', [])
    if not candidates:
        return [], None

    candidate = candidates[0]
    gemini_finish = candidate.get('finishReason')
    if gemini_finish in ["SAFETY", "RECITATION", "OTHER"]:
        return [], f"Gemini stream interrupted by safety filters or other reason: {gemini_finish}"

    openai_finish = _map_gemini_finish_reason(gemini_finish)
    content = candidate.get('content', {})
    parts = content.get('parts', [])
    if not parts:
        return [], None

    openai_chunks: list[dict] = []
    current_tool_calls = []
    for part in parts:
        text = part.get('text', '')
        thought_val = part.get('thought')
        is_thought = thought_val is not None

        if is_thought:
            thought_text = text if text else (thought_val if isinstance(thought_val, str) else "")
            if thought_text:
                openai_chunks.append(
                    _build_openai_stream_chunk(
                        raw_model=raw_model,
                        delta={"reasoning_content": thought_text},
                        finish_reason=openai_finish,
                    )
                )
            continue

        if text:
            openai_chunks.append(
                _build_openai_stream_chunk(
                    raw_model=raw_model,
                    delta={"content": text},
                    finish_reason=openai_finish,
                )
            )

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

        openai_chunks.append(
            _build_openai_stream_chunk(
                raw_model=raw_model,
                delta={"tool_calls": openai_tool_calls},
                finish_reason=openai_finish or "tool_calls",
            )
        )

    return openai_chunks, None


def _extract_usage_update_from_gemini_chunk(chunk_data: dict) -> dict | None:
    usage_meta = chunk_data.get('usageMetadata', {})
    if not usage_meta:
        return None

    usage_update = {
        "prompt_tokens": usage_meta.get('promptTokenCount', 0),
        "completion_tokens": usage_meta.get('candidatesTokenCount', 0),
        "total_tokens": usage_meta.get('totalTokenCount', 0),
    }
    thoughts_token_count = usage_meta.get('thoughtsTokenCount')
    if thoughts_token_count is not None:
        usage_update["reasoning_tokens"] = thoughts_token_count

    return usage_update


def _merge_usage_accumulated(usage_accumulated: dict, usage_update: dict) -> None:
    usage_accumulated["prompt_tokens"] = usage_update.get("prompt_tokens", 0)
    usage_accumulated["completion_tokens"] = usage_update.get("completion_tokens", 0)
    usage_accumulated["total_tokens"] = usage_update.get("total_tokens", 0)

    reasoning_tokens = usage_update.get("reasoning_tokens")
    if reasoning_tokens is not None:
        usage_accumulated.setdefault("completion_tokens_details", {})
        usage_accumulated["completion_tokens_details"]["reasoning_tokens"] = reasoning_tokens


def _build_gemini_config(data: dict) -> dict:
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

    reasoning_effort = data.get('reasoning_effort')
    max_thinking_tokens = data.get('modelMaxThinkingTokens') or data.get('max_completion_tokens')
    if reasoning_effort or max_thinking_tokens or data.get('enableReasoningEffort'):
        thinking_config = {
            "includeThoughts": True
        }
        if max_thinking_tokens:
            thinking_config["thinkingBudget"] = int(max_thinking_tokens)

        gemini_config["thinkingConfig"] = thinking_config

    return gemini_config


def _build_gemini_tools(data: dict) -> list:
    tools = data.get('tools', [])
    if not tools:
        return []

    declarations = []
    for tool in tools:
        if tool.get('type') == 'function':
            func = tool.get('function', {})
            declarations.append({
                "name": func.get('name'),
                "description": func.get('description'),
                "parameters": clean_gemini_schema(func.get('parameters'))
            })

    if not declarations:
        return []
    return [{"function_declarations": declarations}]


def _build_chat_request_context() -> ChatRequestContext:
    data = request.json
    if not isinstance(data, dict):
        data = {}

    raw_model = data.get('model', DEFAULT_QUOTA_MODEL)
    target_model = map_model_name(raw_model)
    messages = data.get('messages', [])
    stream = data.get('stream', False)
    stream_options = data.get('stream_options', {})
    include_usage = stream_options.get('include_usage', False) if stream else False

    logger.info(f"[REQ] Model: {raw_model} -> {target_model} | Stream: {stream} | Usage: {include_usage}")

    contents, system_instruction = transform_openai_to_gemini(messages)
    contents = sanitize_data(contents)
    if system_instruction:
        system_instruction = sanitize_string(system_instruction)

    gemini_config = _build_gemini_config(data)
    gemini_tools = _build_gemini_tools(data)

    is_qwen_quota_mode = _is_qwen_quota_model(raw_model)
    is_gemini_quota_mode = _is_gemini_quota_model(raw_model)
    is_quota_mode = is_qwen_quota_mode or is_gemini_quota_mode

    return ChatRequestContext(
        data=data,
        raw_model=raw_model,
        target_model=target_model,
        messages=messages,
        stream=stream,
        include_usage=include_usage,
        contents=contents,
        system_instruction=system_instruction,
        gemini_config=gemini_config,
        gemini_tools=gemini_tools,
        is_qwen_quota_mode=is_qwen_quota_mode,
        is_gemini_quota_mode=is_gemini_quota_mode,
        is_quota_mode=is_quota_mode,
    )


def _prepare_qwen_quota_upstream(ctx: ChatRequestContext) -> UpstreamRequestContext:
    try:
        selected_account = quota_account_router.select_account("qwen", ctx.target_model)
    except AllAccountsExhaustedError:
        raise UpstreamPreparationError("all_accounts_exceed_quota", "quota_exhausted", 429)
    except AccountRouterError as router_error:
        if str(router_error) == "all_accounts_on_cooldown":
            raise UpstreamPreparationError("All quota accounts are temporarily rate-limited", "upstream_error", 429)
        raise

    account = selected_account.account
    try:
        qwen_creds = refresh_qwen_credentials_file(account.credentials_path)
    except Exception as e:
        raise UpstreamPreparationError(f"Qwen OAuth refresh failed: {e}", "auth_error", 401)

    token = qwen_creds.get("access_token")
    resource_url = qwen_creds.get("resource_url")
    if not token or not resource_url:
        raise UpstreamPreparationError(
            "Qwen OAuth credentials must include access_token and resource_url",
            "auth_error",
            401,
        )

    payload = _qwen_payload_from_openai(ctx.data, ctx.target_model)
    url = _qwen_completion_url(resource_url)
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    return UpstreamRequestContext(
        token=token,
        payload=payload,
        url=url,
        headers=headers,
        params={},
        selected_account=selected_account,
        quota_request_payload=None,
        session_id=None,
        user_prompt_id=None,
    )


def _prepare_gemini_quota_upstream(ctx: ChatRequestContext) -> UpstreamRequestContext:
    try:
        selected_account = quota_account_router.select_account("gemini", ctx.target_model)
    except AllAccountsExhaustedError:
        raise UpstreamPreparationError("all_accounts_exceed_quota", "quota_exhausted", 429)
    except AccountRouterError as router_error:
        if str(router_error) == "all_accounts_on_cooldown":
            raise UpstreamPreparationError("All quota accounts are temporarily rate-limited", "upstream_error", 429)
        raise

    account = selected_account.account
    if not isinstance(account, GeminiAccount):
        raise UpstreamPreparationError("Invalid Gemini account configuration", "config_error", 500)

    auth_lock = get_auth_lock()
    with auth_lock:
        token = get_gemini_access_token_from_file(account.credentials_path)

    session_id = ctx.data.get("session_id") or request.headers.get("x-session-id") or generate_session_id()
    user_prompt_id = ctx.data.get("user_prompt_id") or request.headers.get("x-user-prompt-id") or generate_user_prompt_id()

    quota_request_payload = {
        "contents": ctx.contents,
        "generationConfig": ctx.gemini_config,
    }
    if ctx.gemini_tools:
        quota_request_payload["tools"] = ctx.gemini_tools
    if ctx.system_instruction:
        quota_request_payload["systemInstruction"] = {"parts": [{"text": ctx.system_instruction}]}

    payload = build_quota_payload(
        model=ctx.target_model,
        project=account.project_id,
        request_payload=quota_request_payload,
        user_prompt_id=user_prompt_id,
        session_id=session_id,
    )

    url = f"{CLOUD_CODE_ENDPOINT}:{'streamGenerateContent' if ctx.stream else 'generateContent'}"
    params = {"alt": "sse"} if ctx.stream else {}
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    return UpstreamRequestContext(
        token=token,
        payload=payload,
        url=url,
        headers=headers,
        params=params,
        selected_account=selected_account,
        quota_request_payload=quota_request_payload,
        session_id=session_id,
        user_prompt_id=user_prompt_id,
    )


def _prepare_vertex_upstream(ctx: ChatRequestContext) -> UpstreamRequestContext:
    project_id = os.environ.get('VERTEX_PROJECT_ID')
    location = os.environ.get('VERTEX_LOCATION', 'us-central1')
    token = get_vertex_token()

    if not token:
        raise UpstreamPreparationError("Vertex AI Service Account not found.", "auth_error", 500)

    payload = {
        "contents": ctx.contents,
        "generationConfig": ctx.gemini_config
    }

    if ctx.gemini_tools:
        payload["tools"] = ctx.gemini_tools

    if ctx.system_instruction:
        payload["system_instruction"] = {"parts": [{"text": ctx.system_instruction}]}

    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{ctx.target_model}:{'streamGenerateContent' if ctx.stream else 'generateContent'}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "x-goog-user-project": project_id
    }

    return UpstreamRequestContext(
        token=token,
        payload=payload,
        url=url,
        headers=headers,
        params={},
        selected_account=None,
        quota_request_payload=None,
        session_id=None,
        user_prompt_id=None,
    )


def _prepare_upstream_request(ctx: ChatRequestContext) -> UpstreamRequestContext:
    if ctx.is_qwen_quota_mode:
        return _prepare_qwen_quota_upstream(ctx)
    if ctx.is_gemini_quota_mode:
        return _prepare_gemini_quota_upstream(ctx)
    return _prepare_vertex_upstream(ctx)


def _parse_vertex_stream_line(line: str | bytes) -> dict | None:
    if isinstance(line, bytes):
        line = line.decode(errors="ignore")

    clean_line = line.strip().strip(',').strip('[').strip(']')
    if not clean_line:
        return None

    try:
        chunk_data = json.loads(clean_line)
    except Exception:
        return None

    if not isinstance(chunk_data, dict):
        return None
    return chunk_data


def _gemini_chunk_to_sse_events(chunk_data: dict, raw_model: str, usage_accumulated: dict) -> tuple[list[str], str | None]:
    openai_chunks, policy_error = _convert_gemini_stream_chunk(chunk_data, raw_model)
    if policy_error:
        return [], create_openai_error(policy_error, 'policy_violation', 400)

    usage_update = _extract_usage_update_from_gemini_chunk(chunk_data)
    if usage_update:
        _merge_usage_accumulated(usage_accumulated, usage_update)

    events = [
        f"data: {json.dumps(sanitize_data(chunk), ensure_ascii=False)}\n\n"
        for chunk in openai_chunks
    ]
    return events, None


def _build_usage_stream_chunk(raw_model: str, usage_accumulated: dict) -> str:
    usage_chunk = {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": raw_model,
        "choices": [],
        "usage": usage_accumulated,
    }
    return f"data: {json.dumps(sanitize_data(usage_chunk), ensure_ascii=False)}\n\n"


def _build_vertex_generate_url(model: str, stream: bool) -> str:
    location = os.environ.get('VERTEX_LOCATION', 'us-central1')
    project_id = os.environ.get('VERTEX_PROJECT_ID')
    method = 'streamGenerateContent' if stream else 'generateContent'
    return f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model}:{method}"


def _build_fallback_chain(ctx: ChatRequestContext) -> list[str]:
    fallback_chain = [ctx.target_model]
    if not (ctx.is_quota_mode and STRICT_CLI_PARITY) and 'gemini-3-flash' in ctx.target_model:
        fallback_chain.extend(['gemini-2.5-flash', 'gemini-2.5-flash-lite'])
    elif not (ctx.is_quota_mode and STRICT_CLI_PARITY) and 'gemini-3.1-pro' in ctx.target_model:
        fallback_chain.append('gemini-2.5-pro')
    return fallback_chain


def _shape_gemini_nonstream_response(resp_data: dict, raw_model: str) -> tuple[str, int]:
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

        if gemini_finish == "MAX_TOKENS":
            finish_reason = "length"
        elif all_function_calls:
            finish_reason = "tool_calls"

    usage = resp_data.get('usageMetadata', {})

    message_content = {
        "role": "assistant",
        "content": text,
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
                    "arguments": json.dumps(fn.get('args', {})),
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
            "finish_reason": finish_reason,
        }],
        "usage": {
            "prompt_tokens": usage.get('promptTokenCount', 0),
            "completion_tokens": usage.get('candidatesTokenCount', 0),
            "total_tokens": usage.get('totalTokenCount', 0),
        }
    }

    if 'thoughtsTokenCount' in usage:
        openai_response["usage"]["completion_tokens_details"] = {
            "reasoning_tokens": usage['thoughtsTokenCount']
        }

    return json.dumps(sanitize_data(openai_response), ensure_ascii=False), 200


def _execute_non_stream_request(ctx: ChatRequestContext, upstream: UpstreamRequestContext) -> tuple[str, int]:
    fallback_chain = _build_fallback_chain(ctx)

    last_r = None
    resp_data = None

    token = upstream.token
    payload = upstream.payload
    url = upstream.url
    selected_account = upstream.selected_account

    max_attempts = len(fallback_chain)
    if ctx.is_quota_mode and selected_account is not None and selected_account.mode == "rounding":
        max_attempts = max(max_attempts, len(selected_account.pool))

    attempt = 0
    while attempt < max_attempts:
        current_model = fallback_chain[min(attempt, len(fallback_chain) - 1)]
        attempt_payload = payload.copy()
        attempt_url = url

        if ctx.is_quota_mode:
            attempt_payload["model"] = current_model
        else:
            attempt_url = _build_vertex_generate_url(current_model, stream=False)

        if ctx.is_quota_mode:
            if ctx.is_qwen_quota_mode:
                r = send_generate_to_url(
                    token,
                    attempt_payload,
                    attempt_url,
                )
            else:
                r = send_generate(token, attempt_payload)
        else:
            client = get_http_client()
            r = client.post(attempt_url, headers=upstream.headers, json=attempt_payload)

        last_r = r

        if ctx.is_quota_mode and selected_account is not None:
            error_kind = classify_429_response(r.status_code, r.text)
        else:
            error_kind = Quota429Type.NOT_429

        if ctx.is_quota_mode and selected_account is not None and error_kind in {Quota429Type.RATE_LIMIT, Quota429Type.QUOTA_EXHAUSTED}:
            provider = "qwen" if ctx.is_qwen_quota_mode else "gemini"
            event = (
                RotationEvent.RATE_LIMIT
                if error_kind == Quota429Type.RATE_LIMIT
                else RotationEvent.QUOTA_EXHAUSTED
            )
            event_result = quota_account_router.register_event(
                provider=provider,
                account_name=selected_account.account.name,
                mode=selected_account.mode,
                pool=selected_account.pool,
                event=event,
                model=current_model,
            )
            if event_result.all_exhausted:
                return create_openai_error("all_accounts_exceed_quota", "quota_exhausted", 429), 429
            if event_result.all_cooldown:
                return create_openai_error("All quota accounts are temporarily rate-limited", "upstream_error", 429), 429

            if event_result.switched and selected_account.mode == "rounding":
                old_account = selected_account.account.name
                logger.info(f"[{provider}] Account rotation triggered in non-stream, switching from {old_account}")
                selected_account = quota_account_router.select_account(provider, current_model)
                new_account = selected_account.account.name
                logger.info(f"[{provider}] Switched to account {new_account}")

                if provider == "gemini":
                    account = selected_account.account
                    if not isinstance(account, GeminiAccount):
                        return create_openai_error("Invalid Gemini account configuration", "config_error", 500), 500

                    with get_auth_lock():
                        token = get_gemini_access_token_from_file(account.credentials_path)

                    payload = build_quota_payload(
                        model=current_model,
                        project=account.project_id,
                        request_payload=upstream.quota_request_payload or {},
                        user_prompt_id=upstream.user_prompt_id or generate_user_prompt_id(),
                        session_id=upstream.session_id,
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

        if r.status_code == 429 and "capacity" in r.text.lower() and len(fallback_chain) > 1 and not ctx.is_quota_mode:
            logger.warning(f"[WARN] Model {current_model} exhausted (capacity). Trying fallback...")
            attempt += 1
            continue

        if r.status_code != 200:
            logger.error(f"[ERROR] API Error {r.status_code}: {r.text}")
            return create_openai_error(f"Upstream Error: {r.text}", "upstream_error", r.status_code), r.status_code

        try:
            resp_data = r.json()
        except Exception:
            return create_openai_error(f"Upstream Error: {r.text}", "upstream_error", 502), 502

        if ctx.is_quota_mode and selected_account is not None:
            provider = "qwen" if ctx.is_qwen_quota_mode else "gemini"
            quota_account_router.register_success(provider, selected_account.account.name)
        break

    else:
        if last_r is None:
            return create_openai_error("Upstream Error (No attempts executed)", "upstream_error", 500), 500
        return create_openai_error(f"Upstream Error (All fallbacks exhausted): {last_r.text}", "upstream_error", last_r.status_code), last_r.status_code

    if ctx.is_gemini_quota_mode:
        resp_data = unwrap_cloud_code_response(resp_data)

    if ctx.is_qwen_quota_mode:
        if isinstance(resp_data, dict):
            resp_data["model"] = ctx.raw_model
        return json.dumps(sanitize_data(resp_data), ensure_ascii=False), 200

    return _shape_gemini_nonstream_response(resp_data, ctx.raw_model)


def _generate_stream_response(ctx: ChatRequestContext, upstream: UpstreamRequestContext):
    state = StreamRuntimeState(
        token=upstream.token,
        payload=upstream.payload,
        url=upstream.url,
        selected_account=upstream.selected_account,
    )
    usage_accumulated = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

    try:
        if ctx.is_quota_mode:
            if ctx.is_qwen_quota_mode:
                lines = stream_generate_lines_from_url(
                    state.token,
                    state.payload,
                    state.url,
                    params=None,
                )
            else:
                lines = stream_generate_lines(state.token, state.payload)

            for line in lines:
                if ctx.is_qwen_quota_mode and line.startswith("data: "):
                    raw = line[6:].strip()
                    if raw == "[DONE]":
                        if state.selected_account is not None:
                            quota_account_router.register_success("qwen", state.selected_account.account.name)
                        break
                    try:
                        parsed = json.loads(raw)
                    except Exception:
                        continue

                    if isinstance(parsed, dict) and parsed.get("error"):
                        error_text = json.dumps(parsed.get("error"), ensure_ascii=False)
                        if state.selected_account is not None and state.selected_account.mode == "rounding":
                            error_kind = classify_429_error_payload(parsed.get("error"))
                            event = RotationEvent.QUOTA_EXHAUSTED
                            if error_kind == Quota429Type.RATE_LIMIT:
                                event = RotationEvent.RATE_LIMIT
                            event_result = quota_account_router.register_event(
                                provider="qwen",
                                account_name=state.selected_account.account.name,
                                mode=state.selected_account.mode,
                                pool=state.selected_account.pool,
                                event=event,
                                model=ctx.target_model,
                            )
                            if event_result.all_exhausted:
                                yield f"data: {create_openai_error('all_accounts_exceed_quota', 'quota_exhausted', 429)}\n\n"
                                return
                            if event_result.all_cooldown:
                                yield f"data: {create_openai_error('All quota accounts are temporarily rate-limited', 'upstream_error', 429)}\n\n"
                                return
                            if event_result.switched:
                                old_account = state.selected_account.account.name if state.selected_account else "unknown"
                                logger.info(f"[qwen] Account rotation triggered in stream, switching from {old_account}")
                                try:
                                    state.selected_account = quota_account_router.select_account("qwen", ctx.target_model)
                                    new_account = state.selected_account.account.name if state.selected_account else "unknown"
                                    logger.info(f"[qwen] Switched to account {new_account}")
                                except AllAccountsExhaustedError:
                                    yield f"data: {create_openai_error('all_accounts_exceed_quota', 'quota_exhausted', 429)}\n\n"
                                    return
                                except AccountRouterError:
                                    yield f"data: {create_openai_error('All quota accounts are temporarily rate-limited', 'upstream_error', 429)}\n\n"
                                    return

                        yield f"data: {create_openai_error(f'Upstream API Error: {error_text}', 'upstream_error', 429)}\n\n"
                        return

                    openai_chunk = _openai_chunk_from_qwen(parsed, ctx.raw_model)
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

                events, policy_error_payload = _gemini_chunk_to_sse_events(
                    chunk_data=chunk_data,
                    raw_model=ctx.raw_model,
                    usage_accumulated=usage_accumulated,
                )
                for event in events:
                    yield event
                if policy_error_payload:
                    yield f"data: {policy_error_payload}\n\n"
                    return
        else:
            client = get_http_client()
            response = client.stream(
                "POST",
                state.url,
                headers=upstream.headers,
                json=state.payload,
                params=upstream.params,
            )

            with response as r:
                if r.status_code != 200:
                    err_text = r.read().decode()
                    logger.error(f"[ERROR] Stream API Error {r.status_code}: {err_text}")
                    yield f"data: {create_openai_error(f'Upstream API Error: {err_text}', 'upstream_error', r.status_code)}\n\n"
                    return

                for line in r.iter_lines():
                    if not line:
                        continue

                    chunk_data = _parse_vertex_stream_line(line)
                    if not chunk_data:
                        continue

                    events, policy_error_payload = _gemini_chunk_to_sse_events(
                        chunk_data=chunk_data,
                        raw_model=ctx.raw_model,
                        usage_accumulated=usage_accumulated,
                    )
                    for event in events:
                        yield event
                    if policy_error_payload:
                        yield f"data: {policy_error_payload}\n\n"
                        return

        if ctx.include_usage:
            yield _build_usage_stream_chunk(ctx.raw_model, usage_accumulated)

        if ctx.is_gemini_quota_mode and state.selected_account is not None:
            quota_account_router.register_success("gemini", state.selected_account.account.name)

        yield "data: [DONE]\n\n"

    except Exception as e:
        if ctx.is_quota_mode and state.selected_account is not None:
            error_kind = classify_429_exception(e)
            if error_kind in {Quota429Type.RATE_LIMIT, Quota429Type.QUOTA_EXHAUSTED}:
                provider = "qwen" if ctx.is_qwen_quota_mode else "gemini"
                event = (
                    RotationEvent.RATE_LIMIT
                    if error_kind == Quota429Type.RATE_LIMIT
                    else RotationEvent.QUOTA_EXHAUSTED
                )
                event_result = quota_account_router.register_event(
                    provider=provider,
                    account_name=state.selected_account.account.name,
                    mode=state.selected_account.mode,
                    pool=state.selected_account.pool,
                    event=event,
                    model=ctx.target_model,
                )
                if event_result.all_exhausted:
                    yield from _stream_quota_error(
                        create_openai_error("all_accounts_exceed_quota", "quota_exhausted", 429)
                    )
                    return
                if event_result.all_cooldown:
                    yield from _stream_quota_error(
                        create_openai_error("All quota accounts are temporarily rate-limited", "upstream_error", 429)
                    )
                    return
                if event_result.switched and state.selected_account.mode == "rounding":
                    old_account = state.selected_account.account.name
                    logger.info(f"[{provider}] Account rotation triggered in exception handler, switching from {old_account}")
                    try:
                        state.selected_account = quota_account_router.select_account(provider, ctx.target_model)
                        new_account = state.selected_account.account.name
                        logger.info(f"[{provider}] Switched to account {new_account}")
                    except AllAccountsExhaustedError:
                        yield from _stream_quota_error(
                            create_openai_error("all_accounts_exceed_quota", "quota_exhausted", 429)
                        )
                        return
                    except AccountRouterError:
                        yield from _stream_quota_error(
                            create_openai_error("All quota accounts are temporarily rate-limited", "upstream_error", 429)
                        )
                        return

        logger.error(f"[ERROR] Stream Exception: {e}")
        yield f"data: {create_openai_error(str(e), 'stream_exception')}\n\n"

@openai_bp.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    try:
        request_ctx = _build_chat_request_context()
        try:
            upstream_ctx = _prepare_upstream_request(request_ctx)
        except UpstreamPreparationError as prep_error:
            return create_openai_error(prep_error.message, prep_error.error_type, prep_error.status_code), prep_error.status_code

        if request_ctx.stream:
            return Response(
                stream_with_context(_generate_stream_response(request_ctx, upstream_ctx)),
                mimetype='text/event-stream',
            )

        return _execute_non_stream_request(request_ctx, upstream_ctx)

    except Exception as e:
        logger.exception("[ERROR] Internal Proxy Error in chat_completions")
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

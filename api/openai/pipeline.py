from __future__ import annotations

from flask import request

from api.openai.transform import transform_openai_to_gemini
from api.openai.types import ChatRequestContext
from config import DEFAULT_QUOTA_MODEL, STRICT_CLI_PARITY
from core.logging import get_logger
from core.models import map_model_name
from core.utils import sanitize_data, sanitize_string, clean_gemini_schema
from services.quota_transport import generate_session_id, generate_user_prompt_id
from api.openai.providers.google_vertex import GoogleVertexProvider
from api.openai.providers.gemini_cli import GeminiCliProvider
from api.openai.providers.qwen_code import QwenCodeProvider
from api.openai.strategies.direct import DirectStrategy
from api.openai.strategies.rotate_on_429_rounding import RotateOn429RoundingStrategy

logger = get_logger(__name__)


def _is_qwen_quota_model(raw_model: str) -> bool:
    return 'qwen' in raw_model and 'quota' in raw_model


def _is_gemini_quota_model(raw_model: str) -> bool:
    return 'quota' in raw_model and not _is_qwen_quota_model(raw_model)


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


def build_request_context() -> ChatRequestContext:
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

    session_id = data.get("session_id") or request.headers.get("x-session-id") or generate_session_id()
    user_prompt_id = data.get("user_prompt_id") or request.headers.get("x-user-prompt-id") or generate_user_prompt_id()

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
        session_id=session_id,
        user_prompt_id=user_prompt_id,
    )


def resolve_provider(ctx: ChatRequestContext):
    if ctx.is_qwen_quota_mode:
        return QwenCodeProvider()
    if ctx.is_gemini_quota_mode:
        return GeminiCliProvider()
    return GoogleVertexProvider()


def resolve_strategy(ctx: ChatRequestContext):
    if ctx.is_quota_mode:
        return RotateOn429RoundingStrategy()
    return DirectStrategy()


def build_fallback_chain(ctx: ChatRequestContext) -> list[str]:
    fallback_chain = [ctx.target_model]
    if not (ctx.is_quota_mode and STRICT_CLI_PARITY) and 'gemini-3-flash' in ctx.target_model:
        fallback_chain.extend(['gemini-2.5-flash', 'gemini-2.5-flash-lite'])
    elif not (ctx.is_quota_mode and STRICT_CLI_PARITY) and 'gemini-3.1-pro' in ctx.target_model:
        fallback_chain.append('gemini-2.5-pro')
    return fallback_chain

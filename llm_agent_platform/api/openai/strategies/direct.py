from __future__ import annotations

import json

from llm_agent_platform.core.utils import create_openai_error
from llm_agent_platform.core.logging import get_logger
from llm_agent_platform.api.openai.providers.base import Provider
from llm_agent_platform.api.openai.types import ChatRequestContext
from llm_agent_platform.api.openai.response_shaper import shape_gemini_nonstream_response
from llm_agent_platform.api.openai.streaming import gemini_chunk_to_sse_events, build_usage_stream_chunk, parse_vertex_stream_line
from llm_agent_platform.config import STRICT_CLI_PARITY

logger = get_logger(__name__)


class DirectStrategy:
    id = "direct"

    def _build_fallback_chain(self, ctx: ChatRequestContext) -> list[str]:
        fallback_chain = [ctx.target_model]
        if not (ctx.is_quota_mode and STRICT_CLI_PARITY) and 'gemini-3-flash' in ctx.target_model:
            fallback_chain.extend(['gemini-2.5-flash', 'gemini-2.5-flash-lite'])
        elif not (ctx.is_quota_mode and STRICT_CLI_PARITY) and 'gemini-3.1-pro' in ctx.target_model:
            fallback_chain.append('gemini-2.5-pro')
        return fallback_chain

    def execute_non_stream(self, ctx: ChatRequestContext, provider: Provider) -> tuple[str, int]:
        fallback_chain = self._build_fallback_chain(ctx)
        last_status = None
        last_text = ""

        for attempt in range(len(fallback_chain)):
            current_model = fallback_chain[min(attempt, len(fallback_chain) - 1)]
            creds = provider.load_runtime_credentials(None)
            upstream = provider.prepare_upstream(ctx, creds, None, model_override=current_model)
            data, status_code = provider.execute_non_stream(ctx, upstream)

            if isinstance(data, dict):
                data_text = json.dumps(data, ensure_ascii=False)
            else:
                data_text = str(data)

            last_status = status_code
            last_text = data_text

            if status_code == 429 and "capacity" in data_text.lower() and len(fallback_chain) > 1:
                logger.warning(f"[WARN] Model {current_model} exhausted (capacity). Trying fallback...")
                continue

            if status_code != 200:
                return create_openai_error(
                    f"Upstream Error: {data_text}",
                    "upstream_error",
                    status_code,
                ), status_code

            if not isinstance(data, dict):
                return create_openai_error(
                    f"Upstream Error: {data_text}",
                    "upstream_error",
                    502,
                ), 502

            return shape_gemini_nonstream_response(data, ctx.raw_model)

        if last_status is None:
            return create_openai_error("Upstream Error (No attempts executed)", "upstream_error", 500), 500

        return create_openai_error(
            f"Upstream Error (All fallbacks exhausted): {last_text}",
            "upstream_error",
            last_status,
        ), last_status

    def stream(self, ctx: ChatRequestContext, provider: Provider):
        usage_accumulated = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}

        try:
            creds = provider.load_runtime_credentials(None)
            upstream = provider.prepare_upstream(ctx, creds, None)

            for line in provider.stream_lines(ctx, upstream):
                if not line:
                    continue

                chunk_data = parse_vertex_stream_line(line)
                if not chunk_data:
                    continue

                events, policy_error_payload = gemini_chunk_to_sse_events(
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
                yield build_usage_stream_chunk(ctx.raw_model, usage_accumulated)

            yield "data: [DONE]\n\n"

        except Exception as exc:
            from llm_agent_platform.services.quota_transport import parse_stream_exception

            status_code, body = parse_stream_exception(exc)
            if status_code is not None:
                logger.error(f"[ERROR] Stream API Error {status_code}: {body}")
                yield f"data: {create_openai_error(f'Upstream API Error: {body}', 'upstream_error', status_code)}\n\n"
                return

            logger.error(f"[ERROR] Stream Exception: {exc}")
            yield f"data: {create_openai_error(str(exc), 'stream_exception')}\n\n"

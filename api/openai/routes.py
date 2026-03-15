import json
from flask import Blueprint, Response, stream_with_context

from auth.credentials import get_auth_availability
from core.logging import get_logger
from core.utils import create_openai_error
from api.openai.pipeline import build_request_context, resolve_provider, resolve_strategy
from api.openai.types import UpstreamPreparationError

openai_bp = Blueprint('openai', __name__)
logger = get_logger(__name__)


@openai_bp.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    try:
        request_ctx = build_request_context()
        provider = resolve_provider(request_ctx)
        strategy = resolve_strategy(request_ctx)

        if request_ctx.stream:
            return Response(
                stream_with_context(strategy.stream(request_ctx, provider)),
                mimetype='text/event-stream',
            )

        return strategy.execute_non_stream(request_ctx, provider)

    except UpstreamPreparationError as prep_error:
        return create_openai_error(prep_error.message, prep_error.error_type, prep_error.status_code), prep_error.status_code
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

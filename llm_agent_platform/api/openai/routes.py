import json
from flask import Blueprint, Response, stream_with_context

from llm_agent_platform.auth.credentials import get_auth_availability
from llm_agent_platform.core.logging import get_logger
from llm_agent_platform.core.utils import create_openai_error
from llm_agent_platform.api.openai.pipeline import build_request_context, resolve_provider, resolve_strategy
from llm_agent_platform.services.provider_registry import get_provider_registry
from llm_agent_platform.api.openai.types import UpstreamPreparationError
from llm_agent_platform.services.account_router import AccountRouterError, quota_account_router

openai_bp = Blueprint('openai', __name__)
logger = get_logger(__name__)


@openai_bp.route('/v1/chat/completions', methods=['POST'])
@openai_bp.route('/<group_id>/v1/chat/completions', methods=['POST'])
def chat_completions(group_id: str | None = None):
    try:
        request_ctx = build_request_context()
        if group_id is not None:
            request_ctx.group_id = group_id
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
        logger.exception("[ERROR] Internal Gateway Error in chat_completions")
        return create_openai_error(f"Internal Gateway Error: {str(e)}", "internal_error", 500), 500

def _resolve_group_models(group_id: str) -> list[str] | None:
    models: list[str] = []
    group_config_present = False
    for provider in ("gemini_cli", "qwen_code"):
        try:
            cfg = quota_account_router._load_provider_config(provider)
        except AccountRouterError:
            continue
        if cfg.groups:
            group_config_present = True
            group = cfg.groups.get(group_id)
            if group and group.models:
                models.extend(group.models)

    if group_config_present:
        return models
    return None


@openai_bp.route('/v1/models', methods=['GET'])
@openai_bp.route('/<group_id>/v1/models', methods=['GET'])
def list_models(group_id: str | None = None):
    group_id = group_id or "g0"
    models = _resolve_group_models(group_id)
    if models is None:
        availability = get_auth_availability()
        models = get_provider_registry().list_models_for_availability(availability)

    return json.dumps({"data": [{"id": m, "object": "model"} for m in models]})

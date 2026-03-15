from __future__ import annotations

from typing import Iterable, Any

from api.openai.providers.base import Provider, ProviderRuntimeCreds
from api.openai.types import ChatRequestContext, UpstreamRequestContext, UpstreamPreparationError
from auth.qwen_oauth import refresh_qwen_credentials_file
from services.quota_transport import send_generate_to_url, stream_generate_lines_from_url


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


class QwenCodeProvider(Provider):
    id = "qwen_code"

    def load_runtime_credentials(self, account) -> ProviderRuntimeCreds:
        try:
            qwen_creds = refresh_qwen_credentials_file(account.credentials_path)
        except Exception as exc:
            raise UpstreamPreparationError(f"Qwen OAuth refresh failed: {exc}", "auth_error", 401)

        token = qwen_creds.get("access_token")
        resource_url = qwen_creds.get("resource_url")
        if not token or not resource_url:
            raise UpstreamPreparationError(
                "Qwen OAuth credentials must include access_token and resource_url",
                "auth_error",
                401,
            )

        return ProviderRuntimeCreds(token=token, resource_url=resource_url)

    def prepare_upstream(
        self,
        ctx: ChatRequestContext,
        creds: ProviderRuntimeCreds,
        account,
        model_override: str | None = None,
    ) -> UpstreamRequestContext:
        payload = _qwen_payload_from_openai(ctx.data, model_override or ctx.target_model)
        url = _qwen_completion_url(creds.resource_url or "")
        headers = {
            "Authorization": f"Bearer {creds.token}",
            "Content-Type": "application/json",
        }
        return UpstreamRequestContext(
            token=creds.token,
            payload=payload,
            url=url,
            headers=headers,
            params={},
            selected_account=None,
            quota_request_payload=None,
            session_id=ctx.session_id,
            user_prompt_id=ctx.user_prompt_id,
        )

    def execute_non_stream(
        self,
        ctx: ChatRequestContext,
        upstream: UpstreamRequestContext,
    ) -> tuple[Any, int]:
        response = send_generate_to_url(
            upstream.token,
            upstream.payload,
            upstream.url,
        )
        try:
            data = response.json()
        except Exception:
            data = response.text
        return data, response.status_code

    def stream_lines(
        self,
        ctx: ChatRequestContext,
        upstream: UpstreamRequestContext,
    ) -> Iterable[str | bytes]:
        return stream_generate_lines_from_url(
            upstream.token,
            upstream.payload,
            upstream.url,
            params=None,
        )

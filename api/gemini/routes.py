import os
import json
from flask import Blueprint, request, Response, stream_with_context
from config import CLOUD_CODE_ENDPOINT
from auth.credentials import (
    get_auth_lock,
    get_gemini_access_token_from_file,
    get_vertex_token,
)
from core.models import map_model_name
from core.utils import create_openai_error
from services.http_pool import get_http_client
from services.account_router import (
    AccountRouterError,
    AllAccountsExhaustedError,
    GeminiAccount,
    RotationEvent,
    quota_account_router,
)
from services.quota_transport import (
    build_quota_payload,
    classify_429_exception,
    classify_429_response,
    generate_session_id,
    generate_user_prompt_id,
    Quota429Type,
    parse_cloud_code_sse_line,
    send_generate,
    stream_generate_lines,
    unwrap_cloud_code_response,
)

gemini_bp = Blueprint('gemini', __name__)

@gemini_bp.route('/v1beta/models/<model_id>:<action>', methods=['POST'])
@gemini_bp.route('/v1/models/<model_id>:<action>', methods=['POST'])
def gemini_proxy(model_id, action):
    """
    Native Gemini API Proxy.
    Supports :generateContent and :streamGenerateContent actions.
    """
    try:
        # Map model ID if needed (though native clients usually send correct IDs)
        # But we might want to support our custom quota/vertex suffixes here too
        target_model = map_model_name(model_id)
        
        # Determine mode based on model ID suffix
        is_quota_mode = 'quota' in model_id
        
        # Prepare request
        url = ""
        headers = {}
        payload = request.get_json(silent=True) or {}
        quota_request_payload = payload
        params = request.args.to_dict() # Pass through query params (like alt=sse)
        selected_account = None
        session_id = None
        user_prompt_id = None

        if is_quota_mode:
            # --- Gemini CLI / Cloud Code Emulation Mode ---
            try:
                selected_account = quota_account_router.select_account("gemini", target_model)
            except AllAccountsExhaustedError:
                return create_openai_error("all_accounts_exceed_quota", "quota_exhausted", 429), 429
            except AccountRouterError as router_error:
                if str(router_error) == "all_accounts_on_cooldown":
                    return create_openai_error(
                        "All quota accounts are temporarily rate-limited",
                        "upstream_error",
                        429,
                    ), 429
                raise

            account = selected_account.account
            if not isinstance(account, GeminiAccount):
                return create_openai_error("Invalid Gemini account configuration", "config_error", 500), 500

            with get_auth_lock():
                token = get_gemini_access_token_from_file(account.credentials_path)

            session_id = request.headers.get("x-session-id") or request.args.get("session_id") or quota_request_payload.get("session_id") or generate_session_id()
            user_prompt_id = request.headers.get("x-user-prompt-id") or request.args.get("user_prompt_id") or generate_user_prompt_id()

            wrapped_payload = build_quota_payload(
                model=target_model,
                project=account.project_id,
                request_payload=quota_request_payload,
                user_prompt_id=user_prompt_id,
                session_id=session_id,
            )

            url = f"{CLOUD_CODE_ENDPOINT}:{action}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            # Use wrapped payload
            payload = wrapped_payload

        else:
            # --- Standard Vertex AI Mode ---
            project_id = os.environ.get('VERTEX_PROJECT_ID')
            location = os.environ.get('VERTEX_LOCATION', 'us-central1')
            token = get_vertex_token()
            
            if not token:
                 return create_openai_error("Vertex AI Service Account not found.", "auth_error", 500), 500

            url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{target_model}:{action}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "x-goog-user-project": project_id
            }

        # Execute Request
        if action == 'streamGenerateContent':
            def generate_stream():
                try:
                    if is_quota_mode:
                        max_attempts = len(selected_account.pool) if selected_account and selected_account.mode == "rounding" else 1
                        attempts = 0

                        while attempts < max_attempts:
                            try:
                                for line in stream_generate_lines(token, payload):
                                    chunk_data = parse_cloud_code_sse_line(line)
                                    if not chunk_data:
                                        continue
                                    if chunk_data.get("done"):
                                        if selected_account is not None:
                                            quota_account_router.register_success("gemini", selected_account.account.name)
                                        yield "data: [DONE]\n\n"
                                        return
                                    yield f"data: {json.dumps(chunk_data)}\n\n"

                                if selected_account is not None:
                                    quota_account_router.register_success("gemini", selected_account.account.name)
                                return
                            except Exception as stream_error:
                                err_text = str(stream_error)
                                error_kind = classify_429_exception(stream_error)

                                if error_kind in {Quota429Type.RATE_LIMIT, Quota429Type.QUOTA_EXHAUSTED} and selected_account is not None:
                                    event = (
                                        RotationEvent.RATE_LIMIT
                                        if error_kind == Quota429Type.RATE_LIMIT
                                        else RotationEvent.QUOTA_EXHAUSTED
                                    )
                                    event_result = quota_account_router.register_event(
                                        provider="gemini",
                                        account_name=selected_account.account.name,
                                        mode=selected_account.mode,
                                        pool=selected_account.pool,
                                        event=event,
                                        model=target_model,
                                    )
                                    if event_result.all_exhausted:
                                        yield f"data: {create_openai_error('all_accounts_exceed_quota', 'quota_exhausted', 429)}\n\n"
                                        return
                                    if event_result.all_cooldown:
                                        yield f"data: {create_openai_error('All quota accounts are temporarily rate-limited', 'upstream_error', 429)}\n\n"
                                        return
                                    if event_result.switched and selected_account.mode == "rounding":
                                        attempts += 1
                                        selected_account = quota_account_router.select_account("gemini", target_model)
                                        next_account = selected_account.account
                                        if not isinstance(next_account, GeminiAccount):
                                            yield f"data: {create_openai_error('Invalid Gemini account configuration', 'config_error', 500)}\n\n"
                                            return
                                        with get_auth_lock():
                                            token = get_gemini_access_token_from_file(next_account.credentials_path)
                                        payload = build_quota_payload(
                                            model=target_model,
                                            project=next_account.project_id,
                                            request_payload=quota_request_payload,
                                            user_prompt_id=user_prompt_id or generate_user_prompt_id(),
                                            session_id=session_id,
                                        )
                                        continue

                                yield f"data: {create_openai_error(f'Upstream API Error: {err_text}', 'upstream_error', 502)}\n\n"
                                return
                    else:
                        client = get_http_client()
                        with client.stream("POST", url, headers=headers, json=payload, params=params) as r:
                            if r.status_code != 200:
                                err_text = r.read().decode()
                                print(f"[ERROR] Stream API Error {r.status_code}: {err_text}", flush=True)
                                yield f"data: {json.dumps({'error': {'code': r.status_code, 'message': err_text}})}\n\n"
                                return

                            for line in r.iter_lines():
                                if not line:
                                    continue
                                out = line.decode() if isinstance(line, bytes) else line
                                yield out + "\n"

                except Exception as e:
                    print(f"[ERROR] Stream Exception: {e}", flush=True)
                    yield f"data: {json.dumps({'error': {'message': str(e)}})}\n\n"

            return Response(stream_with_context(generate_stream()), mimetype='text/event-stream')
        
        else:
            # Non-streaming
            if is_quota_mode:
                max_attempts = len(selected_account.pool) if selected_account and selected_account.mode == "rounding" else 1
                attempts = 0
                r = None

                while attempts < max_attempts:
                    r = send_generate(token, payload)
                    error_kind = classify_429_response(r.status_code, r.text)
                    if error_kind in {Quota429Type.RATE_LIMIT, Quota429Type.QUOTA_EXHAUSTED} and selected_account is not None:
                        event = (
                            RotationEvent.RATE_LIMIT
                            if error_kind == Quota429Type.RATE_LIMIT
                            else RotationEvent.QUOTA_EXHAUSTED
                        )
                        event_result = quota_account_router.register_event(
                            provider="gemini",
                            account_name=selected_account.account.name,
                            mode=selected_account.mode,
                            pool=selected_account.pool,
                            event=event,
                            model=target_model,
                        )
                        if event_result.all_exhausted:
                            return create_openai_error("all_accounts_exceed_quota", "quota_exhausted", 429), 429
                        if event_result.all_cooldown:
                            return create_openai_error("All quota accounts are temporarily rate-limited", "upstream_error", 429), 429
                        if event_result.switched and selected_account.mode == "rounding":
                            attempts += 1
                            selected_account = quota_account_router.select_account("gemini", target_model)
                            next_account = selected_account.account
                            if not isinstance(next_account, GeminiAccount):
                                return create_openai_error("Invalid Gemini account configuration", "config_error", 500), 500
                            with get_auth_lock():
                                token = get_gemini_access_token_from_file(next_account.credentials_path)
                            payload = build_quota_payload(
                                model=target_model,
                                project=next_account.project_id,
                                request_payload=quota_request_payload,
                                user_prompt_id=user_prompt_id or generate_user_prompt_id(),
                                session_id=session_id,
                            )
                            continue

                    break

                if r is None:
                    return create_openai_error("Upstream Error (No attempts executed)", "upstream_error", 500), 500
            else:
                client = get_http_client()
                r = client.post(url, headers=headers, json=payload, params=params)

            if r.status_code != 200:
                return Response(r.content, status=r.status_code, mimetype='application/json')

            resp_data = r.json()

            if is_quota_mode:
                if selected_account is not None:
                    quota_account_router.register_success("gemini", selected_account.account.name)
                resp_data = unwrap_cloud_code_response(resp_data)

            return json.dumps(resp_data), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return create_openai_error(f"Internal Proxy Error: {str(e)}", "internal_error", 500), 500

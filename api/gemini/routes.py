import os
import json
import httpx
from flask import Blueprint, request, Response, stream_with_context
from config import CLOUD_CODE_ENDPOINT
from auth.credentials import get_user_creds, get_auth_lock, get_vertex_token
from auth.discovery import discover_project_id
from core.models import map_model_name
from core.utils import create_openai_error

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
        payload = request.json
        params = request.args.to_dict() # Pass through query params (like alt=sse)

        if is_quota_mode:
            # --- Gemini CLI / Cloud Code Emulation Mode ---
            user_creds = get_user_creds()
            auth_lock = get_auth_lock()
            with auth_lock:
                if not user_creds:
                    return create_openai_error("Authentication not initialized. Please run auth script.", "auth_error", 401), 401
                token = user_creds.token
            
            project_id = discover_project_id(token)
            if not project_id:
                return create_openai_error("Google Cloud Project ID not found. Set GOOGLE_CLOUD_PROJECT env var.", "config_error", 500), 500

            # Cloud Code API Payload Wrapper
            # Native clients send the raw request body. Cloud Code expects it wrapped.
            wrapped_payload = {
                "model": target_model,
                "project": project_id,
                "request": payload
            }

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
                client = httpx.Client(timeout=60.0)
                try:
                    # Pass params (like alt=sse)
                    with client.stream("POST", url, headers=headers, json=payload, params=params) as r:
                        if r.status_code != 200:
                            err_text = r.read().decode()
                            print(f"[ERROR] Stream API Error {r.status_code}: {err_text}", flush=True)
                            # Return error as JSON data chunk if possible, or just text
                            yield f"data: {json.dumps({'error': {'code': r.status_code, 'message': err_text}})}\n\n"
                            return

                        for line in r.iter_lines():
                            if not line: continue
                            
                            # Pass through SSE lines directly
                            # Cloud Code returns "data: {...}"
                            # Vertex returns JSON array elements if not alt=sse, but usually clients request alt=sse
                            
                            if is_quota_mode:
                                # Cloud Code wraps response in "response" field
                                if line.startswith("data: "):
                                    data_str = line[6:].strip()
                                    if data_str == "[DONE]": 
                                        yield line + "\n"
                                        break
                                    try:
                                        chunk_data = json.loads(data_str)
                                        # Unwrap Cloud Code response wrapper
                                        real_data = chunk_data.get("response", chunk_data)
                                        yield f"data: {json.dumps(real_data)}\n\n"
                                    except: 
                                        yield line + "\n" # Fallback
                                else:
                                    yield line + "\n"
                            else:
                                # Vertex AI direct proxy
                                yield line + "\n"

                except Exception as e:
                    print(f"[ERROR] Stream Exception: {e}", flush=True)
                    yield f"data: {json.dumps({'error': {'message': str(e)}})}\n\n"
                finally:
                    client.close()

            return Response(stream_with_context(generate_stream()), mimetype='text/event-stream')
        
        else:
            # Non-streaming
            with httpx.Client(timeout=60.0) as client:
                r = client.post(url, headers=headers, json=payload, params=params)
                
                if r.status_code != 200:
                    return Response(r.content, status=r.status_code, mimetype='application/json')
                
                resp_data = r.json()
                
                if is_quota_mode:
                    # Unwrap Cloud Code response
                    resp_data = resp_data.get("response", resp_data)
                
                return json.dumps(resp_data), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return create_openai_error(f"Internal Proxy Error: {str(e)}", "internal_error", 500), 500
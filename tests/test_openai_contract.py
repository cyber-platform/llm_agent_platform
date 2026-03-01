import json
import threading
import unittest
from unittest.mock import patch

from main import app
from services.account_router import BaseAccount, GeminiAccount, SelectedAccount


class FakeResponse:
    def __init__(self, status_code: int, payload: dict | None = None, text: str | None = None):
        self.status_code = status_code
        self._payload = payload
        self.text = text if text is not None else (json.dumps(payload, ensure_ascii=False) if payload is not None else "")
        self.content = self.text.encode("utf-8")

    def json(self):
        if self._payload is None:
            raise ValueError("No JSON payload")
        return self._payload


def _parse_sse_json_chunks(raw_stream: str) -> list[dict]:
    chunks: list[dict] = []
    for frame in raw_stream.split("\n\n"):
        frame = frame.strip()
        if not frame.startswith("data: "):
            continue
        payload = frame[6:].strip()
        if payload == "[DONE]":
            continue
        try:
            chunks.append(json.loads(payload))
        except json.JSONDecodeError:
            continue
    return chunks


class OpenAIContractTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @staticmethod
    def _gemini_selected_account(mode: str = "single", name: str = "acct-1", project_id: str = "demo-project") -> SelectedAccount:
        account = GeminiAccount(
            name=name,
            credentials_path=f"secrets/{name}.json",
            project_id=project_id,
        )
        pool = ["acct-1"] if mode == "single" else ["acct-1", "acct-2"]
        return SelectedAccount(
            provider="gemini",
            mode=mode,
            account=account,
            pool=pool,
        )

    @staticmethod
    def _qwen_selected_account(mode: str = "single", name: str = "acct-1") -> SelectedAccount:
        account = BaseAccount(
            name=name,
            credentials_path=f"secrets/{name}.json",
        )
        pool = ["acct-1"] if mode == "single" else ["acct-1", "acct-2"]
        return SelectedAccount(
            provider="qwen",
            mode=mode,
            account=account,
            pool=pool,
        )

    @patch("api.openai.routes.quota_account_router.select_account")
    @patch("api.openai.routes.get_gemini_access_token_from_file", return_value="token-123")
    @patch("api.openai.routes.get_auth_lock", return_value=threading.Lock())
    @patch("api.openai.routes.send_generate")
    def test_non_stream_text_usage_contract(self, mock_send_generate, _mock_lock, _mock_token, mock_select_account):
        mock_select_account.return_value = self._gemini_selected_account()
        mock_send_generate.return_value = FakeResponse(
            200,
            {
                "response": {
                    "candidates": [
                        {
                            "content": {"parts": [{"text": "hello from gemini"}]},
                            "finishReason": "STOP",
                        }
                    ],
                    "usageMetadata": {
                        "promptTokenCount": 12,
                        "candidatesTokenCount": 8,
                        "totalTokenCount": 20,
                    },
                }
            },
        )

        response = self.client.post(
            "/v1/chat/completions",
            json={
                "model": "gemini-3-flash-preview-quota",
                "messages": [{"role": "user", "content": "hello"}],
                "stream": False,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = json.loads(response.data.decode("utf-8"))
        self.assertEqual(body["object"], "chat.completion")
        self.assertEqual(body["choices"][0]["message"]["content"], "hello from gemini")
        self.assertEqual(body["choices"][0]["finish_reason"], "stop")
        self.assertEqual(body["usage"]["prompt_tokens"], 12)
        self.assertEqual(body["usage"]["completion_tokens"], 8)
        self.assertEqual(body["usage"]["total_tokens"], 20)

    @patch("api.openai.routes.quota_account_router.select_account")
    @patch("api.openai.routes.get_gemini_access_token_from_file", return_value="token-123")
    @patch("api.openai.routes.get_auth_lock", return_value=threading.Lock())
    @patch("api.openai.routes.stream_generate_lines")
    def test_stream_usage_chunk_and_done(self, mock_stream_generate_lines, _mock_lock, _mock_token, mock_select_account):
        mock_select_account.return_value = self._gemini_selected_account()
        mock_stream_generate_lines.return_value = iter(
            [
                'data: {"response":{"candidates":[{"content":{"parts":[{"text":"hel"}]}}],"usageMetadata":{"promptTokenCount":3,"candidatesTokenCount":1,"totalTokenCount":4}}}',
                'data: {"response":{"candidates":[{"content":{"parts":[{"text":"lo"}]},"finishReason":"STOP"}],"usageMetadata":{"promptTokenCount":3,"candidatesTokenCount":2,"totalTokenCount":5}}}',
                "data: [DONE]",
            ]
        )

        response = self.client.post(
            "/v1/chat/completions",
            json={
                "model": "gemini-3-flash-preview-quota",
                "messages": [{"role": "user", "content": "hello"}],
                "stream": True,
                "stream_options": {"include_usage": True},
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.data.decode("utf-8")
        self.assertIn("data: [DONE]", payload)

        chunks = _parse_sse_json_chunks(payload)
        content = ""
        usage_chunk = None
        for chunk in chunks:
            choices = chunk.get("choices", [])
            if not choices and "usage" in chunk:
                usage_chunk = chunk
                continue
            if choices:
                content += choices[0].get("delta", {}).get("content", "")

        self.assertEqual(content, "hello")
        self.assertIsNotNone(usage_chunk)
        self.assertEqual(usage_chunk["usage"]["total_tokens"], 5)

    @patch("api.openai.routes.quota_account_router.select_account")
    @patch("api.openai.routes.get_gemini_access_token_from_file", return_value="token-123")
    @patch("api.openai.routes.get_auth_lock", return_value=threading.Lock())
    @patch("api.openai.routes.send_generate")
    def test_non_stream_upstream_error_mapped_to_openai_shape(self, mock_send_generate, _mock_lock, _mock_token, mock_select_account):
        mock_select_account.return_value = self._gemini_selected_account()
        mock_send_generate.return_value = FakeResponse(503, payload=None, text="backend unavailable")

        response = self.client.post(
            "/v1/chat/completions",
            json={
                "model": "gemini-3-flash-preview-quota",
                "messages": [{"role": "user", "content": "ping"}],
                "stream": False,
            },
        )

        self.assertEqual(response.status_code, 503)
        body = json.loads(response.data.decode("utf-8"))
        self.assertIn("error", body)
        self.assertEqual(body["error"]["type"], "upstream_error")
        self.assertEqual(body["error"]["code"], 503)

    @patch("api.openai.routes.quota_account_router.select_account")
    @patch("api.openai.routes.quota_account_router.all_accounts_exhausted", return_value=False)
    @patch("api.openai.routes.quota_account_router.register_quota_limit", return_value=True)
    @patch("api.openai.routes.get_gemini_access_token_from_file", return_value="token-123")
    @patch("api.openai.routes.get_auth_lock", return_value=threading.Lock())
    @patch("api.openai.routes.send_generate")
    def test_non_stream_quota_rotation_contract(
        self,
        mock_send_generate,
        _mock_lock,
        _mock_token,
        _mock_register_quota_limit,
        _mock_all_exhausted,
        mock_select_account,
    ):
        mock_select_account.side_effect = [
            self._gemini_selected_account(mode="rounding", name="acct-1", project_id="p1"),
            self._gemini_selected_account(mode="rounding", name="acct-2", project_id="p2"),
        ]
        mock_send_generate.side_effect = [
            FakeResponse(429, payload=None, text="quota exceeded"),
            FakeResponse(
                200,
                {
                    "response": {
                        "candidates": [
                            {
                                "content": {"parts": [{"text": "rotated hello"}]},
                                "finishReason": "STOP",
                            }
                        ],
                        "usageMetadata": {
                            "promptTokenCount": 10,
                            "candidatesTokenCount": 4,
                            "totalTokenCount": 14,
                        },
                    }
                },
            ),
        ]

        response = self.client.post(
            "/v1/chat/completions",
            json={
                "model": "gemini-3-flash-preview-quota",
                "messages": [{"role": "user", "content": "hello"}],
                "stream": False,
            },
        )

        self.assertEqual(response.status_code, 200)
        body = json.loads(response.data.decode("utf-8"))
        self.assertEqual(body["object"], "chat.completion")
        self.assertEqual(body["choices"][0]["message"]["content"], "rotated hello")
        self.assertEqual(body["usage"]["total_tokens"], 14)
        self.assertEqual(mock_send_generate.call_count, 2)
        self.assertEqual(mock_select_account.call_count, 2)

    @patch("api.openai.routes.quota_account_router.select_account")
    @patch(
        "api.openai.routes.refresh_qwen_credentials_file",
        return_value={
            "access_token": "qwen-token",
            "resource_url": "https://dashscope.aliyuncs.com/compatible-mode",
        },
    )
    @patch("api.openai.routes.stream_generate_lines_from_url")
    def test_stream_quota_rotation_usage_contract(
        self,
        mock_stream_generate_lines,
        _mock_refresh,
        mock_select_account,
    ):
        mock_select_account.return_value = self._qwen_selected_account(mode="rounding")
        mock_stream_generate_lines.return_value = iter(
            [
                'data: {"id":"chatcmpl-q1","choices":[{"index":0,"delta":{"content":"hel"},"finish_reason":null}],"usage":{"prompt_tokens":3,"completion_tokens":1,"total_tokens":4}}',
                'data: {"id":"chatcmpl-q1","choices":[{"index":0,"delta":{"content":"lo"},"finish_reason":"stop"}],"usage":{"prompt_tokens":3,"completion_tokens":2,"total_tokens":5}}',
                "data: [DONE]",
            ]
        )

        response = self.client.post(
            "/v1/chat/completions",
            json={
                "model": "qwen-coder-model-quota",
                "messages": [{"role": "user", "content": "hello"}],
                "stream": True,
                "stream_options": {"include_usage": True},
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.data.decode("utf-8")
        self.assertIn("data: [DONE]", payload)

        chunks = _parse_sse_json_chunks(payload)
        content = ""
        usage_chunk = None
        for chunk in chunks:
            choices = chunk.get("choices", [])
            if not choices and "usage" in chunk:
                usage_chunk = chunk
                continue
            if choices:
                content += choices[0].get("delta", {}).get("content", "")

        self.assertEqual(content, "hello")
        self.assertIsNotNone(usage_chunk)
        self.assertEqual(usage_chunk["usage"]["total_tokens"], 5)

import json
import tempfile
import threading
import unittest
from unittest.mock import patch
from pathlib import Path

from main import app
from auth.credentials import AuthAvailability
from services.account_router import AllAccountsExhaustedError, GeminiAccount, SelectedAccount


class FakeResponse:
    def __init__(
        self,
        status_code: int,
        payload: dict | None = None,
        text: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        self.status_code = status_code
        self._payload = payload
        self.text = text if text is not None else (json.dumps(payload, ensure_ascii=False) if payload is not None else "")
        self.content = self.text.encode("utf-8")
        self.headers = headers or {"content-type": "application/json"}

    def json(self):
        if self._payload is None:
            raise ValueError("No JSON payload")
        return self._payload


class FakeStreamResponse(FakeResponse):
    def __init__(self, status_code: int, lines: list[str | bytes], text: str | None = None):
        super().__init__(status_code=status_code, payload=None, text=text)
        self._lines = lines

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def iter_lines(self):
        for line in self._lines:
            yield line

    def read(self):
        return self.content


class FakeHttpClient:
    def __init__(self, post_response: FakeResponse | None = None, stream_response: FakeStreamResponse | None = None):
        self.post_response = post_response
        self.stream_response = stream_response
        self.last_post_call: dict | None = None
        self.last_stream_call: dict | None = None

    def post(self, url, headers=None, content=None, params=None):
        self.last_post_call = {
            "url": url,
            "headers": headers,
            "content": content,
            "params": params,
        }
        return self.post_response

    def stream(self, method, url, headers=None, content=None, params=None):
        self.last_stream_call = {
            "method": method,
            "url": url,
            "headers": headers,
            "content": content,
            "params": params,
        }
        return self.stream_response


class RefactorP2RoutesTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    @staticmethod
    def _write_json(path: Path, payload: dict) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _selected_gemini_account() -> SelectedAccount:
        return SelectedAccount(
            provider="gemini",
            mode="single",
            account=GeminiAccount(
                name="acct-1",
                credentials_path="secrets/acct-1.json",
                project_id="demo-project",
            ),
            pool=["acct-1"],
            model="gemini-3-flash-preview",
        )

    @patch(
        "api.openai.routes.get_auth_availability",
        return_value=AuthAvailability(
            gemini_quota=True,
            qwen_quota=True,
            vertex=False,
            diagnostics=[],
        ),
    )
    def test_smoke_import_and_models_endpoint(self, _mock_availability):
        self.assertIsNotNone(app)

        response = self.client.get("/v1/models")
        self.assertEqual(response.status_code, 200)

        payload = json.loads(response.data.decode("utf-8"))
        model_ids = {item["id"] for item in payload["data"]}

        self.assertIn("gemini-3-flash-preview-quota", model_ids)
        self.assertIn("qwen-coder-model-quota", model_ids)

    def test_group_aware_models_endpoint(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            gemini_path = tmp_dir / "gemini_accounts_config.json"
            qwen_path = tmp_dir / "qwen_accounts_config.json"

            gemini_cfg = {
                "mode": "single",
                "active_account": "lisa",
                "all_accounts": ["lisa"],
                "accounts": {
                    "lisa": {
                        "credentials_path": "secrets/gemini_lisa.json",
                        "project_id": "project-lisa",
                    }
                },
                "rotation_policy": {
                    "rate_limit_threshold": 2,
                    "quota_exhausted_threshold": 2,
                    "rate_limit_cooldown_seconds": 5,
                },
                "model_quota_resets": {
                    "default": "00:00:00",
                },
            }
            qwen_cfg = {
                "mode": "rounding",
                "active_account": "lisa",
                "all_accounts": ["lisa", "petr"],
                "groups": {
                    "g1": {
                        "accounts": ["lisa"],
                        "models": ["qwen-g1-model-quota"],
                    },
                    "g2": {
                        "accounts": ["petr"],
                        "models": ["qwen-g2-model-quota"],
                    },
                },
                "accounts": {
                    "lisa": {"credentials_path": "secrets/qwen_lisa.json"},
                    "petr": {"credentials_path": "secrets/qwen_petr.json"},
                },
                "rotation_policy": {
                    "rate_limit_threshold": 2,
                    "quota_exhausted_threshold": 2,
                    "rate_limit_cooldown_seconds": 5,
                },
                "model_quota_resets": {
                    "default": "00:00:00",
                },
            }

            self._write_json(gemini_path, gemini_cfg)
            self._write_json(qwen_path, qwen_cfg)

            with (
                patch("services.account_router.GEMINI_ACCOUNTS_CONFIG_PATH", str(gemini_path)),
                patch("services.account_router.QWEN_ACCOUNTS_CONFIG_PATH", str(qwen_path)),
            ):
                g1_response = self.client.get("/g1/v1/models")
                self.assertEqual(g1_response.status_code, 200)
                g1_payload = json.loads(g1_response.data.decode("utf-8"))
                g1_ids = {item["id"] for item in g1_payload["data"]}
                self.assertEqual(g1_ids, {"qwen-g1-model-quota"})

                g2_response = self.client.get("/g2/v1/models")
                self.assertEqual(g2_response.status_code, 200)
                g2_payload = json.loads(g2_response.data.decode("utf-8"))
                g2_ids = {item["id"] for item in g2_payload["data"]}
                self.assertEqual(g2_ids, {"qwen-g2-model-quota"})

    @patch("api.gemini.routes.quota_account_router.select_account")
    @patch("api.gemini.routes.get_gemini_access_token_from_file", return_value="token-123")
    @patch("api.gemini.routes.get_auth_lock", return_value=threading.Lock())
    @patch("api.gemini.routes.send_generate")
    def test_gemini_native_nonstream_quota_success(
        self,
        mock_send_generate,
        _mock_lock,
        _mock_token,
        mock_select_account,
    ):
        mock_select_account.return_value = self._selected_gemini_account()
        mock_send_generate.return_value = FakeResponse(
            200,
            {
                "response": {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {"text": "hello from native gemini"},
                                ]
                            },
                            "finishReason": "STOP",
                        }
                    ],
                    "usageMetadata": {
                        "promptTokenCount": 3,
                        "candidatesTokenCount": 5,
                        "totalTokenCount": 8,
                    },
                }
            },
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            gemini_path = tmp_dir / "gemini_accounts_config.json"
            self._write_json(
                gemini_path,
                {
                    "mode": "single",
                    "active_account": "acct-1",
                    "all_accounts": ["acct-1"],
                    "accounts": {
                        "acct-1": {
                            "credentials_path": "secrets/acct-1.json",
                            "project_id": "demo-project",
                        }
                    },
                    "rotation_policy": {
                        "rate_limit_threshold": 2,
                        "quota_exhausted_threshold": 2,
                        "rate_limit_cooldown_seconds": 5,
                    },
                    "model_quota_resets": {
                        "default": "00:00:00",
                    },
                },
            )
            with patch("services.account_router.GEMINI_ACCOUNTS_CONFIG_PATH", str(gemini_path)):
                response = self.client.post(
                    "/v1/models/gemini-3-flash-preview-quota:generateContent",
                    json={
                        "contents": [{"role": "user", "parts": [{"text": "hello"}]}],
                    },
                )

        self.assertEqual(response.status_code, 200)
        body = json.loads(response.data.decode("utf-8"))
        self.assertIn("candidates", body)
        self.assertEqual(body["candidates"][0]["content"]["parts"][0]["text"], "hello from native gemini")

    @patch("api.gemini.routes.quota_account_router.select_account", side_effect=AllAccountsExhaustedError("all_accounts_exceed_quota"))
    def test_gemini_native_quota_all_accounts_exhausted(self, _mock_select_account):
        response = self.client.post(
            "/v1/models/gemini-3-flash-preview-quota:generateContent",
            json={"contents": [{"role": "user", "parts": [{"text": "hi"}]}]},
        )

        self.assertEqual(response.status_code, 429)
        body = json.loads(response.data.decode("utf-8"))
        self.assertEqual(body["error"]["message"], "all_accounts_exceed_quota")
        self.assertEqual(body["error"]["code"], 429)

    @patch("api.gemini.routes.quota_account_router.select_account")
    @patch("api.gemini.routes.quota_account_router.register_success")
    @patch("api.gemini.routes.get_gemini_access_token_from_file", return_value="token-123")
    @patch("api.gemini.routes.get_auth_lock", return_value=threading.Lock())
    @patch("api.gemini.routes.stream_generate_lines")
    def test_gemini_native_stream_quota_yields_done(
        self,
        mock_stream_generate_lines,
        _mock_lock,
        _mock_token,
        mock_register_success,
        mock_select_account,
    ):
        mock_select_account.return_value = self._selected_gemini_account()
        mock_stream_generate_lines.return_value = iter(
            [
                'data: {"response":{"candidates":[{"content":{"parts":[{"text":"hel"}]}}]}}',
                'data: {"response":{"candidates":[{"content":{"parts":[{"text":"lo"}]},"finishReason":"STOP"}]}}',
                "data: [DONE]",
            ]
        )

        response = self.client.post(
            "/v1/models/gemini-3-flash-preview-quota:streamGenerateContent",
            json={"contents": [{"role": "user", "parts": [{"text": "hello"}]}]},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.data.decode("utf-8")
        self.assertIn("data: [DONE]", payload)
        self.assertIn("\"candidates\"", payload)
        mock_register_success.assert_called_once()

    @patch("api.parity.routes.get_http_client")
    def test_parity_relay_nonstream_forwards_body_and_params(self, mock_get_http_client):
        fake_client = FakeHttpClient(
            post_response=FakeResponse(
                200,
                payload={"ok": True},
                headers={"content-type": "application/json"},
            )
        )
        mock_get_http_client.return_value = fake_client

        response = self.client.post(
            "/parity-relay/v1internal:generateContent?alt=json",
            data=json.dumps({"message": "hello"}),
            content_type="application/json",
            headers={"Authorization": "Bearer parity-token"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.data.decode("utf-8")), {"ok": True})
        self.assertIsNotNone(fake_client.last_post_call)
        self.assertEqual(fake_client.last_post_call["params"], {"alt": "json"})
        self.assertEqual(fake_client.last_post_call["content"], b'{"message": "hello"}')

    @patch("api.parity.routes.get_http_client")
    def test_parity_relay_stream_mode_returns_sse(self, mock_get_http_client):
        fake_client = FakeHttpClient(
            stream_response=FakeStreamResponse(
                200,
                lines=[
                    'data: {"delta":"hel"}',
                    'data: {"delta":"lo"}',
                    "data: [DONE]",
                ],
            )
        )
        mock_get_http_client.return_value = fake_client

        response = self.client.post(
            "/parity-relay/v1internal:streamGenerateContent?alt=sse",
            data="{}",
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.mimetype, "text/event-stream")

        payload = response.data.decode("utf-8")
        self.assertIn('data: {"delta":"hel"}', payload)
        self.assertIn("data: [DONE]", payload)
        self.assertEqual(fake_client.last_stream_call["method"], "POST")


if __name__ == "__main__":
    unittest.main()

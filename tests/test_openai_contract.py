import json
import tempfile
import threading
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

from contextlib import contextmanager

from main import app
from services.account_router import BaseAccount, GeminiAccount, SelectedAccount
from services.account_router import AccountRouterError
from services.account_state_store import AccountStatePaths
from api.openai.providers.qwen_code import QwenCodeProvider


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
    @contextmanager
    def _patched_paths(tmp_dir: Path, gemini_path: Path | None = None, qwen_path: Path | None = None):
        patches = []
        if gemini_path is not None:
            patches.append(
                patch("services.account_router.GEMINI_ACCOUNTS_CONFIG_PATH", str(gemini_path))
            )
        if qwen_path is not None:
            patches.append(
                patch("services.account_router.QWEN_ACCOUNTS_CONFIG_PATH", str(qwen_path))
            )
        patches.append(
            patch(
                "services.account_router.AccountStatePaths",
                new=lambda provider_id, account_name, root_dir=Path("."): AccountStatePaths(
                    provider_id=provider_id,
                    account_name=account_name,
                    root_dir=tmp_dir,
                ),
            )
        )
        if not patches:
            yield
            return

        with patches[0]:
            for ctx in patches[1:]:
                ctx.__enter__()
            try:
                yield
            finally:
                for ctx in reversed(patches[1:]):
                    ctx.__exit__(None, None, None)

    @staticmethod
    def _write_json(path, payload: dict) -> None:
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _gemini_config() -> dict:
        return {
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
        }

    @staticmethod
    def _qwen_config() -> dict:
        return {
            "mode": "single",
            "active_account": "acct-1",
            "all_accounts": ["acct-1"],
            "accounts": {
                "acct-1": {"credentials_path": "secrets/acct-1.json"},
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

    @patch("api.openai.strategies.rotate_on_429_rounding.quota_account_router.select_account")
    @patch("api.openai.providers.gemini_cli.get_gemini_access_token_from_file", return_value="token-123")
    @patch("api.openai.providers.gemini_cli.get_auth_lock", return_value=threading.Lock())
    @patch("api.openai.providers.gemini_cli.send_generate")
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

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            gemini_path = tmp_dir / "gemini_accounts_config.json"
            self._write_json(gemini_path, self._gemini_config())
            with self._patched_paths(tmp_dir, gemini_path=gemini_path, qwen_path=gemini_path):
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

    @patch("api.openai.strategies.rotate_on_429_rounding.quota_account_router.select_account")
    @patch("api.openai.providers.gemini_cli.get_gemini_access_token_from_file", return_value="token-123")
    @patch("api.openai.providers.gemini_cli.get_auth_lock", return_value=threading.Lock())
    @patch("api.openai.providers.gemini_cli.stream_generate_lines")
    def test_stream_usage_chunk_and_done(self, mock_stream_generate_lines, _mock_lock, _mock_token, mock_select_account):
        mock_select_account.return_value = self._gemini_selected_account()
        mock_stream_generate_lines.return_value = iter(
            [
                'data: {"response":{"candidates":[{"content":{"parts":[{"text":"hel"}]}}],"usageMetadata":{"promptTokenCount":3,"candidatesTokenCount":1,"totalTokenCount":4}}}',
                'data: {"response":{"candidates":[{"content":{"parts":[{"text":"lo"}]},"finishReason":"STOP"}],"usageMetadata":{"promptTokenCount":3,"candidatesTokenCount":2,"totalTokenCount":5}}}',
                "data: [DONE]",
            ]
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            gemini_path = tmp_dir / "gemini_accounts_config.json"
            self._write_json(gemini_path, self._gemini_config())
            with self._patched_paths(tmp_dir, gemini_path=gemini_path, qwen_path=gemini_path):
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

    @patch("api.openai.strategies.rotate_on_429_rounding.quota_account_router.select_account")
    @patch("api.openai.providers.gemini_cli.get_gemini_access_token_from_file", return_value="token-123")
    @patch("api.openai.providers.gemini_cli.get_auth_lock", return_value=threading.Lock())
    @patch("api.openai.providers.gemini_cli.send_generate")
    def test_non_stream_upstream_error_mapped_to_openai_shape(self, mock_send_generate, _mock_lock, _mock_token, mock_select_account):
        mock_select_account.return_value = self._gemini_selected_account()
        mock_send_generate.return_value = FakeResponse(503, payload=None, text="backend unavailable")

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            gemini_path = tmp_dir / "gemini_accounts_config.json"
            self._write_json(gemini_path, self._gemini_config())
            with self._patched_paths(tmp_dir, gemini_path=gemini_path, qwen_path=gemini_path):
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

    @patch("api.openai.strategies.rotate_on_429_rounding.quota_account_router.select_account")
    @patch(
        "api.openai.strategies.rotate_on_429_rounding.quota_account_router.register_event",
        return_value=type(
            "EventResult",
            (),
            {"switched": True, "all_exhausted": False, "all_cooldown": False},
        )(),
    )
    @patch("api.openai.providers.gemini_cli.get_gemini_access_token_from_file", return_value="token-123")
    @patch("api.openai.providers.gemini_cli.get_auth_lock", return_value=threading.Lock())
    @patch("api.openai.providers.gemini_cli.send_generate")
    def test_non_stream_quota_rotation_contract(
        self,
        mock_send_generate,
        _mock_lock,
        _mock_token,
        _mock_register_event,
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

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            gemini_path = tmp_dir / "gemini_accounts_config.json"
            self._write_json(gemini_path, self._gemini_config())
            with self._patched_paths(tmp_dir, gemini_path=gemini_path, qwen_path=gemini_path):
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

    @patch(
        "api.openai.strategies.rotate_on_429_rounding.quota_account_router.select_account",
        side_effect=AccountRouterError("all accounts on cooldown please wait 4"),
    )
    def test_all_cooldown_message_contract(self, _mock_select_account):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            gemini_path = tmp_dir / "gemini_accounts_config.json"
            self._write_json(gemini_path, self._gemini_config())
            with self._patched_paths(tmp_dir, gemini_path=gemini_path, qwen_path=gemini_path):
                response = self.client.post(
                    "/v1/chat/completions",
                    json={
                        "model": "gemini-3-flash-preview-quota",
                        "messages": [{"role": "user", "content": "ping"}],
                        "stream": False,
                    },
                )

                self.assertEqual(response.status_code, 429)
                body = json.loads(response.data.decode("utf-8"))
        self.assertIn("error", body)
        self.assertIn("all accounts on cooldown please wait 4", body["error"]["message"])

    @patch("api.openai.providers.qwen_code.read_qwen_credentials")
    @patch("api.openai.providers.qwen_code.refresh_qwen_credentials_file")
    @patch("api.openai.providers.qwen_code.load_last_used_at")
    def test_qwen_idle_refresh_triggers_refresh(
        self,
        mock_load_last_used,
        mock_refresh,
        mock_read,
    ):
        account = BaseAccount(name="acct-1", credentials_path="secrets/qwen.json")
        last_used = datetime.now(tz=timezone.utc) - timedelta(seconds=1000)
        mock_load_last_used.return_value = last_used
        mock_refresh.return_value = {
            "access_token": "qwen-token",
            "resource_url": "https://dashscope.aliyuncs.com/compatible-mode",
        }
        mock_read.side_effect = AssertionError("read_qwen_credentials should not be called")

        provider = QwenCodeProvider()
        creds = provider.load_runtime_credentials(account)

        self.assertEqual(creds.token, "qwen-token")
        self.assertEqual(creds.resource_url, "https://dashscope.aliyuncs.com/compatible-mode")
        self.assertEqual(mock_refresh.call_count, 1)

    @patch("api.openai.strategies.rotate_on_429_rounding.quota_account_router.select_account")
    @patch(
        "api.openai.providers.qwen_code.refresh_qwen_credentials_file",
        return_value={
            "access_token": "qwen-token",
            "resource_url": "https://dashscope.aliyuncs.com/compatible-mode",
        },
    )
    @patch("api.openai.providers.qwen_code.stream_generate_lines_from_url")
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

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            qwen_path = tmp_dir / "qwen_accounts_config.json"
            self._write_json(qwen_path, self._qwen_config())
            with self._patched_paths(tmp_dir, qwen_path=qwen_path, gemini_path=qwen_path):
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

    @patch("api.openai.strategies.rotate_on_429_rounding.quota_account_router.select_account")
    @patch("api.openai.providers.qwen_code.save_last_used_at")
    @patch("api.openai.providers.qwen_code.send_generate_to_url")
    @patch("api.openai.providers.qwen_code.read_qwen_credentials")
    @patch("api.openai.providers.qwen_code.refresh_qwen_credentials_file")
    @patch("api.openai.providers.qwen_code.load_last_used_at")
    def test_qwen_refresh_and_retry_on_401(
        self,
        mock_load_last_used,
        mock_refresh,
        mock_read,
        mock_send_generate,
        _mock_touch,
        mock_select_account,
    ):
        mock_select_account.return_value = self._qwen_selected_account(mode="single")
        mock_load_last_used.return_value = datetime.now(tz=timezone.utc)
        mock_read.return_value = {
            "access_token": "qwen-token",
            "resource_url": "https://dashscope.aliyuncs.com/compatible-mode",
        }
        mock_refresh.return_value = {
            "access_token": "qwen-token-2",
            "resource_url": "https://dashscope.aliyuncs.com/compatible-mode",
        }
        mock_send_generate.side_effect = [
            FakeResponse(401, payload={"error": "unauthorized"}),
            FakeResponse(
                200,
                payload={
                    "id": "chatcmpl-q1",
                    "choices": [
                        {"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}
                    ],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                },
            ),
        ]

        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            qwen_path = tmp_dir / "qwen_accounts_config.json"
            self._write_json(qwen_path, self._qwen_config())
            with self._patched_paths(tmp_dir, qwen_path=qwen_path, gemini_path=qwen_path):
                response = self.client.post(
                    "/v1/chat/completions",
                    json={
                        "model": "qwen-coder-model-quota",
                        "messages": [{"role": "user", "content": "hello"}],
                        "stream": False,
                    },
                )

                self.assertEqual(response.status_code, 200)
                payload = json.loads(response.data.decode("utf-8"))
        self.assertEqual(payload["model"], "qwen-coder-model-quota")
        self.assertEqual(mock_send_generate.call_count, 2)
        self.assertEqual(mock_refresh.call_count, 1)

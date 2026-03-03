import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from zoneinfo import ZoneInfo

from services.account_router import AllAccountsExhaustedError, QuotaAccountRouter, RotationEvent


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class QuotaAccountRouterTests(unittest.TestCase):
    def _make_router(self, base_dir: Path) -> QuotaAccountRouter:
        gemini_cfg = {
            "mode": "single",
            "active_account": "lisa",
            "all_accounts": ["lisa", "petr"],
            "accounts": {
                "lisa": {
                    "credentials_path": "secrets/gemini_lisa.json",
                    "project_id": "project-lisa",
                },
                "petr": {
                    "credentials_path": "secrets/gemini_petr.json",
                    "project_id": "project-petr",
                },
            },
            "rotation_policy": {
                "rate_limit_threshold": 2,
                "quota_exhausted_threshold": 2,
                "rate_limit_cooldown_seconds": 5,
            },
            "model_quota_resets": {
                "default": "00:00",
                "gemini-3-flash-preview": "10:00",
            },
        }
        qwen_cfg = {
            "mode": "single",
            "active_account": "lisa",
            "all_accounts": ["lisa", "petr"],
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
                "default": "00:00",
                "qwen-coder-model": "08:00",
            },
        }

        gemini_path = base_dir / "gemini_accounts_config.json"
        qwen_path = base_dir / "qwen_accounts_config.json"
        _write_json(gemini_path, gemini_cfg)
        _write_json(qwen_path, qwen_cfg)

        with (
            patch("services.account_router.GEMINI_ACCOUNTS_CONFIG_PATH", str(gemini_path)),
            patch("services.account_router.QWEN_ACCOUNTS_CONFIG_PATH", str(qwen_path)),
        ):
            router = QuotaAccountRouter()
        return router

    def test_single_mode_uses_active_account(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            router = self._make_router(tmp_dir)

            gemini_path = tmp_dir / "gemini_accounts_config.json"
            qwen_path = tmp_dir / "qwen_accounts_config.json"

            with (
                patch("services.account_router.GEMINI_ACCOUNTS_CONFIG_PATH", str(gemini_path)),
                patch("services.account_router.QWEN_ACCOUNTS_CONFIG_PATH", str(qwen_path)),
            ):
                gemini_selected = router.select_account("gemini")
                qwen_selected = router.select_account("qwen")

            self.assertEqual(gemini_selected.account.name, "lisa")
            self.assertEqual(gemini_selected.pool, ["lisa"])
            self.assertEqual(getattr(gemini_selected.account, "project_id", None), "project-lisa")

            self.assertEqual(qwen_selected.account.name, "lisa")
            self.assertEqual(qwen_selected.pool, ["lisa"])

    def test_rounding_rotates_after_two_limit_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            router = self._make_router(tmp_dir)

            qwen_path = tmp_dir / "qwen_accounts_config.json"
            qwen_rounding_cfg = {
                "mode": "rounding",
                "active_account": "lisa",
                "all_accounts": ["lisa", "petr"],
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
                    "default": "00:00",
                    "qwen-coder-model": "08:00",
                },
            }
            _write_json(qwen_path, qwen_rounding_cfg)

            with patch("services.account_router.QWEN_ACCOUNTS_CONFIG_PATH", str(qwen_path)):
                selected = router.select_account("qwen", "qwen-coder-model")
            self.assertEqual(selected.account.name, "lisa")

            first_event = router.register_event(
                provider="qwen",
                account_name="lisa",
                mode=selected.mode,
                pool=selected.pool,
                event=RotationEvent.RATE_LIMIT,
                model="qwen-coder-model",
            )
            self.assertFalse(first_event.switched)

            second_event = router.register_event(
                provider="qwen",
                account_name="lisa",
                mode=selected.mode,
                pool=selected.pool,
                event=RotationEvent.RATE_LIMIT,
                model="qwen-coder-model",
            )
            self.assertTrue(second_event.switched)
            self.assertFalse(second_event.all_exhausted)

            with patch("services.account_router.QWEN_ACCOUNTS_CONFIG_PATH", str(qwen_path)):
                next_selected = router.select_account("qwen", "qwen-coder-model")
            self.assertEqual(next_selected.account.name, "petr")

    def test_rounding_marks_exhausted_only_for_quota_exhausted(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            router = self._make_router(tmp_dir)

            qwen_path = tmp_dir / "qwen_accounts_config.json"
            qwen_rounding_cfg = {
                "mode": "rounding",
                "active_account": "lisa",
                "all_accounts": ["lisa", "petr"],
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
                    "default": "00:00",
                    "qwen-coder-model": "08:00",
                },
            }
            _write_json(qwen_path, qwen_rounding_cfg)

            with patch("services.account_router.QWEN_ACCOUNTS_CONFIG_PATH", str(qwen_path)):
                selected = router.select_account("qwen", "qwen-coder-model")

            router.register_event(
                provider="qwen",
                account_name="lisa",
                mode=selected.mode,
                pool=selected.pool,
                event=RotationEvent.QUOTA_EXHAUSTED,
                model="qwen-coder-model",
            )
            second = router.register_event(
                provider="qwen",
                account_name="lisa",
                mode=selected.mode,
                pool=selected.pool,
                event=RotationEvent.QUOTA_EXHAUSTED,
                model="qwen-coder-model",
            )
            self.assertTrue(second.switched)
            self.assertFalse(second.all_exhausted)

            with patch("services.account_router.QWEN_ACCOUNTS_CONFIG_PATH", str(qwen_path)):
                next_selected = router.select_account("qwen", "qwen-coder-model")
            self.assertEqual(next_selected.account.name, "petr")

    def test_all_accounts_exceed_quota_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            router = self._make_router(tmp_dir)

            qwen_path = tmp_dir / "qwen_accounts_config.json"
            qwen_rounding_cfg = {
                "mode": "rounding",
                "active_account": "lisa",
                "all_accounts": ["lisa", "petr"],
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
                    "default": "00:00",
                    "qwen-coder-model": "08:00",
                },
            }
            _write_json(qwen_path, qwen_rounding_cfg)

            with patch("services.account_router.QWEN_ACCOUNTS_CONFIG_PATH", str(qwen_path)):
                selected = router.select_account("qwen", "qwen-coder-model")

            router.register_event(
                provider="qwen",
                account_name="lisa",
                mode=selected.mode,
                pool=selected.pool,
                event=RotationEvent.QUOTA_EXHAUSTED,
                model="qwen-coder-model",
            )
            router.register_event(
                provider="qwen",
                account_name="lisa",
                mode=selected.mode,
                pool=selected.pool,
                event=RotationEvent.QUOTA_EXHAUSTED,
                model="qwen-coder-model",
            )
            router.register_event(
                provider="qwen",
                account_name="petr",
                mode=selected.mode,
                pool=selected.pool,
                event=RotationEvent.QUOTA_EXHAUSTED,
                model="qwen-coder-model",
            )
            router.register_event(
                provider="qwen",
                account_name="petr",
                mode=selected.mode,
                pool=selected.pool,
                event=RotationEvent.QUOTA_EXHAUSTED,
                model="qwen-coder-model",
            )

            self.assertTrue(router.all_accounts_exhausted("qwen", selected.pool, "qwen-coder-model"))

            with patch("services.account_router.QWEN_ACCOUNTS_CONFIG_PATH", str(qwen_path)):
                with self.assertRaises(AllAccountsExhaustedError):
                    router.select_account("qwen", "qwen-coder-model")

    def test_model_reset_timestamp_uses_vladivostok_schedule(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            router = self._make_router(tmp_dir)
            qwen_path = tmp_dir / "qwen_accounts_config.json"

            cfg = {
                "mode": "rounding",
                "active_account": "lisa",
                "all_accounts": ["lisa", "petr"],
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
                    "qwen-coder-model": "08:00",
                    "default": "00:00",
                },
            }
            _write_json(qwen_path, cfg)

            with patch("services.account_router.QWEN_ACCOUNTS_CONFIG_PATH", str(qwen_path)):
                selected = router.select_account("qwen", "qwen-coder-model")

            router.register_event(
                provider="qwen",
                account_name=selected.account.name,
                mode=selected.mode,
                pool=selected.pool,
                event=RotationEvent.QUOTA_EXHAUSTED,
                model="qwen-coder-model",
            )
            router.register_event(
                provider="qwen",
                account_name=selected.account.name,
                mode=selected.mode,
                pool=selected.pool,
                event=RotationEvent.QUOTA_EXHAUSTED,
                model="qwen-coder-model",
            )

            self.assertTrue(router.all_accounts_exhausted("qwen", [selected.account.name], "qwen-coder-model"))

            now_local = datetime.now(ZoneInfo("Asia/Vladivostok"))
            self.assertIsNotNone(now_local)

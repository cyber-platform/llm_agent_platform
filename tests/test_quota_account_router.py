import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from services.account_router import AllAccountsExhaustedError, QuotaAccountRouter


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
        }
        qwen_cfg = {
            "mode": "single",
            "active_account": "lisa",
            "all_accounts": ["lisa", "petr"],
            "accounts": {
                "lisa": {"credentials_path": "secrets/qwen_lisa.json"},
                "petr": {"credentials_path": "secrets/qwen_petr.json"},
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
            }
            _write_json(qwen_path, qwen_rounding_cfg)

            with patch("services.account_router.QWEN_ACCOUNTS_CONFIG_PATH", str(qwen_path)):
                selected = router.select_account("qwen")
            self.assertEqual(selected.account.name, "lisa")

            switched_1 = router.register_quota_limit("qwen", "lisa", selected.mode, selected.pool)
            self.assertFalse(switched_1)

            switched_2 = router.register_quota_limit("qwen", "lisa", selected.mode, selected.pool)
            self.assertTrue(switched_2)

            with patch("services.account_router.QWEN_ACCOUNTS_CONFIG_PATH", str(qwen_path)):
                next_selected = router.select_account("qwen")
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
            }
            _write_json(qwen_path, qwen_rounding_cfg)

            with patch("services.account_router.QWEN_ACCOUNTS_CONFIG_PATH", str(qwen_path)):
                selected = router.select_account("qwen")

            router.register_quota_limit("qwen", "lisa", selected.mode, selected.pool)
            router.register_quota_limit("qwen", "lisa", selected.mode, selected.pool)
            router.register_quota_limit("qwen", "petr", selected.mode, selected.pool)
            router.register_quota_limit("qwen", "petr", selected.mode, selected.pool)

            self.assertTrue(router.all_accounts_exhausted("qwen", selected.pool))

            with patch("services.account_router.QWEN_ACCOUNTS_CONFIG_PATH", str(qwen_path)):
                with self.assertRaises(AllAccountsExhaustedError):
                    router.select_account("qwen")

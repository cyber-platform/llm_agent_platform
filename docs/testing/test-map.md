# Test Map

## Overview
- Контур покрывает provider-centric OpenAI-compatible контракт, quota-runtime поведение и provider-specific boundaries.
- Трассировка поддерживается на уровне `requirement -> suite -> test script`.

## Suites
| Suite | Requirement | Scripts | Status |
| :--- | :--- | :--- | :--- |
| [`openai-contract.md`](docs/testing/suites/openai-contract.md) | OpenAI stream/non-stream контракт для provider-scoped routes, включая `openai-chatgpt` private backend adapter и streamed error mapping | [`llm_agent_platform/tests/test_openai_contract.py`](llm_agent_platform/tests/test_openai_contract.py:1), [`llm_agent_platform/tests/test_openai_chatgpt_runtime.py`](llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1) | active |
| [`proxy-routes.md`](docs/testing/suites/proxy-routes.md) | Smoke/endpoint покрытие для `/<provider_name>/v1/models`, provider-local groups, native Gemini proxy и parity relay | [`llm_agent_platform/tests/test_refactor_p2_routes.py`](llm_agent_platform/tests/test_refactor_p2_routes.py:1) | active |
| [`provider-catalogs.md`](docs/testing/suites/provider-catalogs.md) | Provider-local catalogs: static bootstrap catalogs и provider-specific catalog boundaries; для `openai-chatgpt` каноничен static catalog baseline | [`llm_agent_platform/tests/test_provider_catalogs.py`](llm_agent_platform/tests/test_provider_catalogs.py:1) | active |
| [`quota-parity.md`](docs/testing/suites/quota-parity.md) | Quota payload parity с `gemini-cli` shape | [`llm_agent_platform/tests/test_quota_transport_parity.py`](llm_agent_platform/tests/test_quota_transport_parity.py:1) | active |
| [`quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md) | Unified quota account rotation для `gemini` и `qwen`: `single/rounding`, switch policies (random, by-N), groups isolation, group-aware provider-scoped `/models`, all-cooldown `please wait <seconds>` | [`llm_agent_platform/tests/test_quota_account_router.py`](llm_agent_platform/tests/test_quota_account_router.py:1), [`llm_agent_platform/tests/test_refactor_p2_routes.py`](llm_agent_platform/tests/test_refactor_p2_routes.py:1), [`llm_agent_platform/tests/test_openai_contract.py`](llm_agent_platform/tests/test_openai_contract.py:1) | active |
| [`quota-state-persistence.md`](docs/testing/suites/quota-state-persistence.md) | Persisted quota state: `STATE_DIR`, `account_state.json`, group snapshot, `quota_scope` (per_model/per_provider), async writer | [`test_quota_account_router.py`](llm_agent_platform/tests/test_quota_account_router.py) | active |
| [`config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md) | Env split `.env`/`.env.oauth` + runtime layout [`llm_agent_platform/`](llm_agent_platform:1) and [`scripts/`](scripts:1) | manual + smoke scripts | planned |

## Runbook
- Запуск: `uv run python -m unittest discover -s llm_agent_platform/tests -p "test_*.py"`
- Быстрая проверка синтаксиса: `uv run python -m compileall llm_agent_platform`
- Тестовые артефакты: используются фиктивные файлы в `secrets_test/`
- Целевая runtime-проверка `openai-chatgpt`: `uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_runtime.py`

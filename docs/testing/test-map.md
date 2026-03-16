# Test Map

## Overview
- Контур покрывает quota-first parity и OpenAI-compatible контракт для Kilo Code.
- Трассировка поддерживается на уровне `requirement -> suite -> test script`.

## Suites
| Suite | Requirement | Scripts | Status |
| :--- | :--- | :--- | :--- |
| [`openai-contract.md`](docs/testing/suites/openai-contract.md) | OpenAI stream/non-stream контракт для Kilo | [`test_openai_contract.py`](tests/test_openai_contract.py) | active |
| [`proxy-routes.md`](docs/testing/suites/proxy-routes.md) | Smoke/endpoint покрытие для импорта приложения, `/v1/models`, native Gemini proxy и parity relay | [`test_refactor_p2_routes.py`](tests/test_refactor_p2_routes.py) | active |
| [`quota-parity.md`](docs/testing/suites/quota-parity.md) | Quota payload parity с `gemini-cli` shape | [`test_quota_transport_parity.py`](tests/test_quota_transport_parity.py) | active |
| [`quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md) | Unified quota account rotation для `gemini` и `qwen`: `single/rounding`, switch policies (random, by-N), groups isolation, group-aware `/v1/models`, all-cooldown `please wait <seconds>` | [`test_quota_account_router.py`](tests/test_quota_account_router.py), [`test_refactor_p2_routes.py`](tests/test_refactor_p2_routes.py), [`test_openai_contract.py`](tests/test_openai_contract.py) | active |
| [`config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md) | Env split `.env`/`.env.oauth` + repo layout `src/` | manual + smoke scripts | planned |

## Runbook
- Запуск: `uv run python -m unittest discover -s tests -p "test_*.py"`
- Быстрая проверка синтаксиса: `uv run python -m compileall api auth core services main.py tests`

# Test Map

## Overview
- Контур покрывает quota-first parity и OpenAI-compatible контракт для Kilo Code.
- Трассировка поддерживается на уровне `requirement -> suite -> test script`.

## Suites
| Suite | Requirement | Scripts | Status |
| :--- | :--- | :--- | :--- |
| [`openai-contract.md`](docs/testing/suites/openai-contract.md) | OpenAI stream/non-stream контракт для Kilo | [`test_openai_contract.py`](tests/test_openai_contract.py) | active |
| [`quota-parity.md`](docs/testing/suites/quota-parity.md) | Quota payload parity с `gemini-cli` shape | [`test_quota_transport_parity.py`](tests/test_quota_transport_parity.py) | active |

## Runbook
- Запуск: `uv run python -m unittest discover -s tests -p "test_*.py"`
- Быстрая проверка синтаксиса: `uv run python -m compileall api auth core services main.py tests`


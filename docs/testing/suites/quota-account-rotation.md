# Suite: Unified quota account rotation

## Scope
- Проверка выбора аккаунта в режиме `single` через `active_account`.
- Проверка переключения в режиме `rounding` после 2 подряд quota-limit ошибок.
- Проверка состояния исчерпания всех аккаунтов (`all_accounts_exceed_quota`).
- Проверка сохранения OpenAI stream/non-stream контракта при ротации.

## Requirement Traceability
- Requirement: unified quota multi-account ротация для `gemini` и `qwen`.
- Task links: [`013-qwen-oauth-multi-account-rotation.md`](tasks_descriptions/tasks/013-qwen-oauth-multi-account-rotation.md)
- Scripts:
  - [`test_quota_account_router.py`](tests/test_quota_account_router.py)
  - [`test_openai_contract.py`](tests/test_openai_contract.py)

## Verification Command
- `uv run python -m unittest tests/test_quota_account_router.py`
- `uv run python -m unittest tests/test_openai_contract.py`

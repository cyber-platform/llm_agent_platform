# Suite: Unified quota account rotation

## Scope
- Проверка выбора аккаунта в режиме `single` через `active_account`.
- Проверка переключения в режиме `rounding` с раздельной реакцией на `rate_limit` (cooldown) и `quota_exhausted` (exhausted-until).
- Проверка состояний `all_accounts_on_cooldown` и `all_accounts_exceed_quota`.
- Проверка сохранения OpenAI stream/non-stream контракта при ротации.

## Contract References
- 429 error contract: [`docs/contracts/api/openai/errors/429-error.schema.json`](../../contracts/api/openai/errors/429-error.schema.json)

## Requirement Traceability
- Requirement: unified quota multi-account ротация для `gemini` и `qwen`.
- Task links: [`013-qwen-oauth-multi-account-rotation.md`](tasks_descriptions/tasks/013-qwen-oauth-multi-account-rotation.md)
- Scripts:
  - [`test_quota_account_router.py`](tests/test_quota_account_router.py)
  - [`test_openai_contract.py`](tests/test_openai_contract.py)

## Verification Command
- `uv run python -m unittest tests/test_quota_account_router.py`
- `uv run python -m unittest tests/test_openai_contract.py`

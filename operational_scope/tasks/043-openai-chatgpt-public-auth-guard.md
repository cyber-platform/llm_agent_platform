# Public auth guard для `openai-chatgpt` OpenAI-compatible API

## Контекст

Для PoC public OpenAI-compatible surface должен принимать только platform API keys, scoped к одной `group_id` внутри `openai-chatgpt`.

Error contract при missing / invalid / revoked / out-of-scope key уже зафиксирован.

## Goal

Добавить в public `openai-chatgpt` routes обязательную проверку Bearer platform API key до выполнения provider pipeline.

## Scope

В scope:

- извлечение Bearer token из `Authorization` header;
- lookup key через registry layer;
- проверка `active/revoked` status;
- проверка provider/group scope against requested route;
- возврат OpenAI-style `401 authentication_error / invalid_api_key`;
- tests для happy-path и auth failures.

Не входит в scope:

- admin CRUD для keys;
- frontend UI;
- admin auth.

## Canonical references

- [`docs/contracts/api/openai/errors/401-invalid-api-key-error.schema.json`](../../docs/contracts/api/openai/errors/401-invalid-api-key-error.schema.json)
- [`docs/architecture/openai-chat-completions-pipeline.md`](../../docs/architecture/openai-chat-completions-pipeline.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`llm_agent_platform/api/openai/routes.py`](../../llm_agent_platform/api/openai/routes.py)

## Dependencies

- Зависит от [`042-openai-chatgpt-api-key-registry-and-admin-crud.md`](042-openai-chatgpt-api-key-registry-and-admin-crud.md).
- Может выполняться параллельно с [`044-admin-monitoring-read-model-and-activate.md`](044-admin-monitoring-read-model-and-activate.md).

## Implementation notes

1. Проверять auth до `build_request_context(...)` или в другом раннем preflight boundary.
2. Для route без явного `group_id` использовать resolved default group semantics текущего provider config.
3. Missing header, malformed bearer token и revoked/out-of-scope key должны сводиться к одному внешнему `401 invalid_api_key` contract.
4. Не использовать platform API keys для admin endpoints.

## Definition of Done

- Public `models` и `chat/completions` routes требуют valid Bearer key.
- Ключ от одной группы не авторизует другую группу.
- Invalid/revoked/missing key возвращает payload по `401-invalid-api-key-error.schema.json`.
- Valid key не ломает существующий provider pipeline.
- Добавлены тесты для positive и negative auth scenarios.

## Execution Status

- Current State: выполнена.
- Next Step: использовать guard как baseline для task 046 и финального PoC smoke/documentation sync в task 047.
- Blockers: none.

## Implementation Summary

- Добавлен ранний public auth guard в [`llm_agent_platform/api/openai/auth_guard.py`](../../llm_agent_platform/api/openai/auth_guard.py:1) для `openai-chatgpt` routes.
- Guard резолвит provider/group через существующий route pipeline boundary, извлекает Bearer token из `Authorization` header и валидирует platform API key через [`OpenAIChatGPTApiKeyRegistryService`](../../llm_agent_platform/services/openai_chatgpt_api_keys.py:50).
- Для route без явного `group_id` используется resolved default-group semantics из route resolver, поэтому key scope проверяется против фактической provider-local group.
- Missing header, malformed bearer token, revoked key и out-of-scope key сведены к одному внешнему OpenAI-style `401` payload с `error.type=authentication_error` и `error.code=invalid_api_key`.
- Admin routes не изменялись и не используют platform API keys как auth substitute.

## Touched Files

- [`llm_agent_platform/api/openai/auth_guard.py`](../../llm_agent_platform/api/openai/auth_guard.py:1)
- [`llm_agent_platform/api/openai/routes.py`](../../llm_agent_platform/api/openai/routes.py:1)
- [`llm_agent_platform/tests/test_openai_chatgpt_runtime.py`](../../llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1)
- [`llm_agent_platform/tests/test_refactor_p2_routes.py`](../../llm_agent_platform/tests/test_refactor_p2_routes.py:1)
- [`docs/testing/suites/openai-contract.md`](../../docs/testing/suites/openai-contract.md:1)
- [`docs/testing/suites/proxy-routes.md`](../../docs/testing/suites/proxy-routes.md:1)

## Verification Performed

- `uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_runtime.py`
- `uv run python -m unittest llm_agent_platform/tests/test_refactor_p2_routes.py`
- `uv run python -m unittest llm_agent_platform/tests/test_admin_api_keys.py`
- `uv run python -m compileall llm_agent_platform`

## Delivered Coverage

- Happy-path authorization for public `models` and `chat/completions` with valid group-scoped platform API key.
- Negative auth scenarios for missing token, malformed bearer token, revoked key and out-of-scope key.
- Regression coverage confirming valid key does not break existing `openai-chatgpt` runtime pipeline behavior.

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

- [`docs/architecture/poc-openai-chatgpt-demo.md`](../../docs/architecture/poc-openai-chatgpt-demo.md)
- [`docs/contracts/api/openai/errors/401-invalid-api-key-error.schema.json`](../../docs/contracts/api/openai/errors/401-invalid-api-key-error.schema.json)
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

- Current State: запланирована.
- Next Step: встроить auth guard после materialization key registry.
- Blockers: зависит от task 042.

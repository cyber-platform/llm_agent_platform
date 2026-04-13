# Admin routes для `openai-chatgpt` capabilities и request policies

## Контекст

Admin API contracts и endpoint semantics для capability read и key-scoped request policies уже канонизированы в `docs/`.

Теперь нужно materialize-ить соответствующие backend routes в admin surface.

## Goal

Добавить в admin API `openai-chatgpt` routes для чтения model capabilities и чтения/сохранения/удаления key-scoped request policies.

## Scope

В scope:

- `GET /admin/model-capabilities/openai-chatgpt/models/<model_id>`;
- `GET /admin/request-policies/openai-chatgpt/keys/<key_id>`;
- `PUT /admin/request-policies/openai-chatgpt/keys/<key_id>`;
- `DELETE /admin/request-policies/openai-chatgpt/keys/<key_id>`;
- wiring existing admin auth guard;
- response/error handling для no-policy, missing key, missing model.

Не входит в scope:

- frontend UI;
- pipeline request rewrite;
- provider adapter changes.

## Canonical references

- [`docs/architecture/provider-request-policy-overrides.md`](../../docs/architecture/provider-request-policy-overrides.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`docs/contracts/api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json`](../../docs/contracts/api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json)
- [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-read.schema.json`](../../docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-read.schema.json)
- [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-request.schema.json`](../../docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-request.schema.json)
- [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-response.schema.json`](../../docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-response.schema.json)
- [`services/backend/llm_agent_platform/api/admin/routes.py`](../../services/backend/llm_agent_platform/api/admin/routes.py)

## Dependencies

- Зависит от capability overlay service.
- Зависит от request policy registry service.

## Implementation notes

1. Empty `model_overrides` response должен явно означать pass-through/no-policy state.
2. `PUT` должен оставаться full replace, без раннего введения partial patch semantics.
3. `DELETE` должен возвращать key в explicit no-policy state.
4. Routes должны следовать current provider-scoped admin path style.

## Definition of Done

- Все четыре admin routes materialized в backend.
- Routes соответствуют canonical schemas и path semantics.
- Error handling различает missing key, missing model и invalid input.
- Есть verification notes для read/upsert/delete behaviors.

## Initial status

- Current State: planned.
- Next Step: materialize admin routes after backend services are ready.
- Blockers: none.

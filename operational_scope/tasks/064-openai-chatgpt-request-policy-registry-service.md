# `openai-chatgpt` request policy registry service

## Контекст

Request policy registry для `openai-chatgpt` уже канонизирован как отдельный mutable artifact в `secrets/openai-chatgpt/policy_registry/registry.json`.

Следующий implementation step — материализовать backend service, который читает, сохраняет, заменяет и удаляет key-scoped policy records.

## Goal

Подготовить backend service layer для работы с `openai-chatgpt` request policy registry как с отдельным key-scoped governance storage.

## Scope

В scope:

- чтение `secrets/openai-chatgpt/policy_registry/registry.json`;
- получение policy record по `key_id`;
- full upsert semantics для одного key;
- delete/reset semantics для одного key;
- structural validation и key/group consistency checks.

Не входит в scope:

- admin routes;
- pipeline request mutation;
- provider adapter mapping;
- UI.

## Canonical references

- [`docs/architecture/provider-request-policy-overrides.md`](../../docs/architecture/provider-request-policy-overrides.md)
- [`docs/contracts/config/openai-chatgpt-request-policy-registry.schema.json`](../../docs/contracts/config/openai-chatgpt-request-policy-registry.schema.json)
- [`docs/examples/openai-chatgpt-request-policy-registry.example.json`](../../docs/examples/openai-chatgpt-request-policy-registry.example.json)
- [`docs/contracts/config/openai-chatgpt-api-key-registry.schema.json`](../../docs/contracts/config/openai-chatgpt-api-key-registry.schema.json)
- [`services/backend/llm_agent_platform/services/openai_chatgpt_api_keys.py`](../../services/backend/llm_agent_platform/services/openai_chatgpt_api_keys.py)

## Dependencies

- Опирается на existing API key registry semantics.
- Является dependency для admin request policy routes и pipeline policy resolution.

## Implementation notes

1. Отсутствие policy record должно означать pass-through mode.
2. Service не должен invent-ить implicit defaults из capability overlay.
3. Validation against capability registry должна учитывать platform configuration toggle.
4. Даже при выключенной capability validation service обязан проверять structural integrity и `key_id/group_id` consistency.

## Definition of Done

- Backend умеет читать, upsert-ить и delete-ить key-scoped request policies.
- `key_id` и `group_id` consistency checks materialized.
- Отсутствие policy корректно возвращается как valid no-policy state.
- Есть verification notes для read/upsert/delete paths.

## Initial status

- Current State: completed.
- Next Step: use the service from admin request policy routes and pipeline policy resolution tasks.
- Blockers: none.

## Execution notes

- Materialized backend service: `services/backend/llm_agent_platform/services/openai_chatgpt_request_policies.py`.
- Added explicit backend config for `OPENAI_CHATGPT_REQUEST_POLICY_REGISTRY_PATH` and `OPENAI_CHATGPT_REQUEST_POLICY_CAPABILITY_VALIDATION_ENABLED` in `services/backend/llm_agent_platform/config.py`.
- Reused existing API key registry semantics by extending `OpenAIChatGPTApiKeyRegistryService` with `get_key_record(key_id)` so policy validation can enforce `key_id/group_id` consistency against the canonical API key registry.
- `get_policy(key_id)` now returns explicit pass-through state with empty `model_overrides` when the key exists but no policy record is stored.
- `upsert_policy(...)` implements full replace semantics for one key, preserves `created_at` on rewrite, refreshes `updated_at`, and writes the registry atomically to `secrets/openai-chatgpt/policy_registry/registry.json`.
- `delete_policy(key_id)` removes the stored record and returns explicit no-policy state for the same key instead of surfacing a missing-policy error.
- Structural validation covers top-level registry shape, per-record `key_id/group_id/model_overrides/updated_at`, allowed override modes, non-empty strings, duplicate `key_id` rejection, and stored-record consistency with the API key registry.
- Capability validation is toggleable and defaults to enabled; when enabled, model ids, parameter families, and values are validated against `OpenAIChatGPTModelCapabilitiesService`, while disabled mode still enforces structural integrity and key/group consistency.
- Added dedicated test suite `services/backend/llm_agent_platform/tests/test_openai_chatgpt_request_policies.py` covering no-policy reads, upsert/delete lifecycle, invalid capability values, group mismatch, and disabled capability validation semantics.
- Updated testing navigation in `docs/testing/test-map.md` and added suite page `docs/testing/suites/openai-chatgpt-request-policies.md`.

## Verification

- `cd services/backend && uv run python -m compileall llm_agent_platform`
- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_request_policies.py`
- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_api_keys.py`
- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_provider_catalogs.py`

## Handoff notes

- Следующий агент может использовать `OpenAIChatGPTRequestPolicyRegistryService` напрямую в task 065 для `GET/PUT/DELETE /admin/request-policies/openai-chatgpt/keys/<key_id>`; `get_policy()` уже отдает explicit no-policy payload, а `delete_policy()` возвращает тот же explicit no-policy state после удаления.
- Для task 065 отдельный synthetic no-policy error не нужен: missing policy record уже трактуется как valid pass-through state, но missing `key_id` по-прежнему должен приходить из `OpenAIChatGPTApiKeyRegistryService` как not-found path.
- Для task 066 service уже дает все нужные normalized data для pipeline resolution: `group_id`, `model_overrides`, `mode`, `value`; pipeline останется только вычислить `effective_request_params` поверх client payload.
- Toggle `OPENAI_CHATGPT_REQUEST_POLICY_CAPABILITY_VALIDATION_ENABLED` влияет только на capability-overlay guardrails; structural validation, allowed override modes и `key_id/group_id` consistency остаются обязательными даже при disabled режиме.
- В disabled capability-validation mode service сознательно допускает future/stale model ids и parameter names, поэтому pipeline/admin routes не должны добавлять hidden implicit validation поверх этого toggle без отдельного архитектурного решения.
- Текущее persistence behavior — atomic full-file rewrite keyed by `key_id`; partial patch semantics, version bump и optimistic locking в эту задачу не входили.

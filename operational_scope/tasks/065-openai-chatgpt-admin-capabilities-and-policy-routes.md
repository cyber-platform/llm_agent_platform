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

- Current State: completed.
- Next Step: use these routes from frontend/admin flows and pipeline-adjacent verification.
- Blockers: none.

## Execution notes

- Materialized four admin endpoints in `services/backend/llm_agent_platform/api/admin/routes.py` for capability read and request policy `GET|PUT|DELETE` under the existing admin JWT guard.
- Added route-local helpers for capability and request policy services plus shared JSON-object payload normalization so malformed/non-object bodies fall into predictable validation errors.
- Reused existing service contracts as-is instead of duplicating policy logic in the route layer: `OpenAIChatGPTModelCapabilitiesService.get_model_capabilities()` drives capability reads, and `OpenAIChatGPTRequestPolicyRegistryService.get_policy()/upsert_policy()/delete_policy()` remain the single source for no-policy, full-replace and reset semantics.
- Route behavior intentionally keeps current backend error envelope style `{"error": <message>}` to stay consistent with the rest of `services/backend/llm_agent_platform/api/admin/routes.py` rather than introducing a task-local response wrapper.
- `GET /admin/model-capabilities/openai-chatgpt/models/<model_id>` now returns `404` for unknown models and `500` for capability-registry read/validation failures.
- `GET /admin/request-policies/openai-chatgpt/keys/<key_id>` now returns explicit no-policy payload for known keys, `404` for unknown keys, and surfaces registry read failures as `500`.
- `PUT /admin/request-policies/openai-chatgpt/keys/<key_id>` preserves full-replace semantics from `OpenAIChatGPTRequestPolicyRegistryService`, returns `404` for unknown keys, and maps invalid group/override payloads to `400`.
- `DELETE /admin/request-policies/openai-chatgpt/keys/<key_id>` returns explicit no-policy state after delete and still distinguishes missing keys with `404`.
- Added focused admin integration suite `services/backend/llm_agent_platform/tests/test_admin_openai_chatgpt_request_policy_routes.py` covering capability read, policy lifecycle, missing model/key handling, and invalid upsert input.
- Updated testing navigation in `docs/testing/test-map.md` and added suite page `docs/testing/suites/admin-openai-chatgpt-policy-routes.md`.

## Handoff notes

- The route layer does not add hidden normalization for policy payloads beyond coercing `group_id` to string and passing through `model_overrides`; any future semantic changes must be made in `services/backend/llm_agent_platform/services/openai_chatgpt_request_policies.py` so admin and pipeline paths stay aligned.
- Unknown `model_id` handling is implemented in the route because `OpenAIChatGPTModelCapabilitiesService.get_model_capabilities()` returns `None` for missing records rather than raising a dedicated not-found exception.
- Unknown `key_id` handling comes from `OpenAIChatGPTApiKeyRegistryService` via `ApiKeyNotFoundError`; read and delete map that to `404`, while `PUT` also returns `404` before request-policy structural validation runs.
- Current `PUT` semantics treat non-object or missing JSON body as invalid input and fall through to service-level validation, which currently surfaces messages like `group_id is required` or `model_overrides must not be empty` with `400`.
- Added test coverage only for the new admin route contour; task 066 can rely on these routes as stable read/write surfaces, but pipeline-specific request mutation still has no coverage in this task and must be added separately.

## Verification

- `cd services/backend && uv run python -m compileall llm_agent_platform`
- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_openai_chatgpt_request_policy_routes.py`
- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_request_policies.py`
- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_api_keys.py`

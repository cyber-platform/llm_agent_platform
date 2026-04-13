# Suite: Admin OpenAI ChatGPT policy routes

## Suite ID
- `TS-ADMIN-OPENAI-CHATGPT-POLICY-ROUTES`

## Documentation roots
- `docs/testing/test-map.md`
- `docs/testing/traceability.md`
- `docs/testing/suites/admin-openai-chatgpt-policy-routes.md`

## Implementation roots
- `services/backend/llm_agent_platform/tests/test_admin_openai_chatgpt_request_policy_routes.py`

## Search anchors
- `TS-ADMIN-OPENAI-CHATGPT-POLICY-ROUTES`
- `test_admin_openai_chatgpt_request_policy_routes.py`
- `admin openai-chatgpt policy routes`
- `model capabilities admin route`

## Scope
- Проверка `GET /admin/model-capabilities/openai-chatgpt/models/<model_id>` для provider-scoped capability read payload.
- Проверка `GET|PUT|DELETE /admin/request-policies/openai-chatgpt/keys/<key_id>` для explicit no-policy, full replace и reset semantics.
- Проверка различения missing `model_id`, missing `key_id` и invalid request policy input.
- Проверка integration wiring между admin auth guard, capability service и request policy registry service.

## Requirement Traceability
- Requirement: backend materialize-ит admin routes для capability read и key-scoped request policy CRUD у `openai-chatgpt`.
- Rollout metadata:
  - suite anchor: `TS-ADMIN-OPENAI-CHATGPT-POLICY-ROUTES`
  - case anchors: `TC-ADMIN-OPENAI-CHATGPT-POLICY-ROUTES-001..002`
- Canonical references:
  - [`docs/architecture/provider-request-policy-overrides.md`](docs/architecture/provider-request-policy-overrides.md:1)
  - [`docs/contracts/api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json`](docs/contracts/api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json:1)
  - [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-read.schema.json`](docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-read.schema.json:1)
  - [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-request.schema.json`](docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-request.schema.json:1)
  - [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-response.schema.json`](docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-response.schema.json:1)
  - [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- Target script: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_openai_chatgpt_request_policy_routes.py`

## Verification Command
- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_openai_chatgpt_request_policy_routes.py`

## Status
- active

# Suite: OpenAI ChatGPT request policies

## Suite ID
- `TS-OPENAI-CHATGPT-REQUEST-POLICIES`

## Documentation roots
- `docs/testing/test-map.md`
- `docs/testing/traceability.md`
- `docs/testing/suites/openai-chatgpt-request-policies.md`

## Implementation roots
- `services/backend/llm_agent_platform/tests/test_openai_chatgpt_request_policies.py`

## Search anchors
- `TS-OPENAI-CHATGPT-REQUEST-POLICIES`
- `test_openai_chatgpt_request_policies.py`
- `openai-chatgpt request policies`
- `request policy registry`

## Scope
- Проверка explicit no-policy read semantics для known `key_id`.
- Проверка full upsert/delete lifecycle для key-scoped request policy registry `openai-chatgpt`.
- Проверка `key_id/group_id` consistency against provider API key registry.
- Проверка capability-overlay-backed validation и toggle semantics для structural-only mode.

## Requirement Traceability
- Requirement: backend materialize-ит key-scoped request policy registry service для `openai-chatgpt`.
- Rollout metadata:
  - suite anchor: `TS-OPENAI-CHATGPT-REQUEST-POLICIES`
  - case anchors: `TC-OPENAI-CHATGPT-REQUEST-POLICIES-001..004`
- Canonical references:
  - [`docs/architecture/provider-request-policy-overrides.md`](docs/architecture/provider-request-policy-overrides.md:1)
  - [`docs/contracts/config/openai-chatgpt-request-policy-registry.schema.json`](docs/contracts/config/openai-chatgpt-request-policy-registry.schema.json:1)
  - [`docs/contracts/config/openai-chatgpt-api-key-registry.schema.json`](docs/contracts/config/openai-chatgpt-api-key-registry.schema.json:1)
  - [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- Target script: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_request_policies.py`

## Verification Command
- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_request_policies.py`

## Status
- active

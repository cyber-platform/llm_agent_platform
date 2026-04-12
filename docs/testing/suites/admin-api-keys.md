# Suite: Admin API keys

## Suite ID
- `TS-ADMIN-API-KEYS`

## Documentation roots
- `docs/testing/test-map.md`
- `docs/testing/traceability.md`
- `docs/testing/suites/admin-api-keys.md`

## Implementation roots
- `services/backend/llm_agent_platform/tests/test_admin_api_keys.py`

## Search anchors
- `TS-ADMIN-API-KEYS`
- `test_admin_api_keys.py`
- `admin api keys`
- `openai-chatgpt api key registry`

## Scope

- Проверка provider-scoped registry для platform API keys `openai-chatgpt`.
- Проверка hash-only persisted storage без сохранения raw secret в `registry.json`.
- Проверка admin CRUD routes `list`, `create`, `revoke` для group-scoped keys.
- Проверка invalid `group_id` handling и исключения revoked key из future lookup path.

## Requirement Traceability

- Requirement: локальный PoC materialize-ит provider-scoped API key registry и admin CRUD для `openai-chatgpt`.
- Rollout metadata:
  - suite anchor: `TS-ADMIN-API-KEYS`
  - case anchors: `TC-ADMIN-API-KEYS-001..003`
- Canonical references:
  - [`docs/contracts/config/openai-chatgpt-api-key-registry.schema.json`](docs/contracts/config/openai-chatgpt-api-key-registry.schema.json:1)
  - [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-request.schema.json`](docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-request.schema.json:1)
  - [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-response.schema.json`](docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-response.schema.json:1)
  - [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-keys-list.schema.json`](docs/contracts/api/admin/api-keys/openai-chatgpt-api-keys-list.schema.json:1)
  - [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-revoke-response.schema.json`](docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-revoke-response.schema.json:1)
  - [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- Target script: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_api_keys.py`

## Verification Command

- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_api_keys.py`

## Status

- active

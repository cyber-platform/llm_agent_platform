# Suite: Admin monitoring refresh

## Suite ID
- `TS-ADMIN-MONITORING-REFRESH`

## Documentation roots
- `docs/testing/test-map.md`
- `docs/testing/traceability.md`
- `docs/testing/suites/admin-monitoring-refresh.md`

## Implementation roots
- `services/backend/llm_agent_platform/tests/test_admin_monitoring_refresh.py`

## Search anchors
- `TS-ADMIN-MONITORING-REFRESH`
- `test_admin_monitoring_refresh.py`
- `admin monitoring refresh`
- `manual refresh`

## Scope

- Проверка provider-wide manual refresh endpoints для `openai-chatgpt`.
- Проверка duplicate-run reuse semantics и progress lifecycle для in-memory refresh manager.
- Проверка terminal outcome aggregation: `completed`, `completed_with_errors`, `error`.
- Проверка enriched provider page fields для `supports_manual_refresh` и group-level refresh summary.
- Проверка canonical mutation order `memory first -> persistence second` для live runtime state.
- Проверка того, что refresh endpoints остаются внутри admin JWT boundary и не используют public API key auth.

## Requirement Traceability

- Requirement: admin monitoring refresh subsystem materialize-ит provider-wide background/manual refresh lifecycle через backend-owned polling flow.
- Rollout metadata:
  - suite anchor: `TS-ADMIN-MONITORING-REFRESH`
  - case anchors: `TC-ADMIN-MONITORING-REFRESH-001..007`
- Canonical references:
  - [`docs/architecture/admin-monitoring-refresh-subsystem.md`](docs/architecture/admin-monitoring-refresh-subsystem.md:1)
  - [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)
  - [`docs/architecture/platform-monitoring-runtime.md`](docs/architecture/platform-monitoring-runtime.md:1)
  - [`docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-start-response.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-start-response.schema.json:1)
  - [`docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-status.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-status.schema.json:1)
  - [`docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json:1)
- Target script: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_monitoring_refresh.py`

## Verification Command

- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_monitoring_refresh.py`

## Status

- active

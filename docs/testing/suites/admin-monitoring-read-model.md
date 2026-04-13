# Suite: Admin monitoring read-model

## Suite ID
- `TS-ADMIN-MONITORING-READ-MODEL`

## Documentation roots
- `docs/testing/test-map.md`
- `docs/testing/traceability.md`
- `docs/testing/suites/admin-monitoring-read-model.md`

## Implementation roots
- `services/backend/llm_agent_platform/tests/test_admin_monitoring_read_model.py`

## Search anchors
- `TS-ADMIN-MONITORING-READ-MODEL`
- `test_admin_monitoring_read_model.py`
- `admin monitoring`
- `read-model`

## Scope

- Проверка динамического `LLM provider` list для admin monitoring shell.
- Проверка `LLM provider`-specific page contract для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1).
- Проверка startup hydration и memory-first read path без request-time reread persisted artifacts.
- Проверка отсутствия legacy `limits.json` dependency в live admin read path.
- Проверка `LLM provider`-specific columns, drawer sections и session-scoped `Activate` semantics.
- Проверка local single-user PoC security boundary и обязательного admin JWT guard для текущего pilot scope.

## Requirement Traceability

- Requirement: admin monitoring surface строится поверх contract-first read-model и `LLM provider`-specific pages.
- Rollout metadata:
  - suite anchor: `TS-ADMIN-MONITORING-READ-MODEL`
  - case anchors: `TC-ADMIN-MONITORING-READ-MODEL-001..005`
- Canonical references:
  - [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)
  - [`docs/architecture/platform-monitoring-runtime.md`](docs/architecture/platform-monitoring-runtime.md:1)
  - [`docs/contracts/api/admin/monitoring/providers-list.schema.json`](docs/contracts/api/admin/monitoring/providers-list.schema.json:1)
  - [`docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json:1)
  - [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- Target script: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_monitoring_read_model.py`

## Verification Command

- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_monitoring_read_model.py`

## Status

- active

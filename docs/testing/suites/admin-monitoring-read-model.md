# Suite: Admin monitoring read-model

## Suite ID
- `TS-ADMIN-MONITORING-READ-MODEL`

## Documentation roots
- `docs/testing/test-map.md`
- `docs/testing/traceability.md`
- `docs/testing/suites/admin-monitoring-read-model.md`

## Implementation roots
- planned `llm_agent_platform/tests/test_admin_monitoring_read_model.py`

## Search anchors
- `TS-ADMIN-MONITORING-READ-MODEL`
- `test_admin_monitoring_read_model.py`
- `admin monitoring`
- `read-model`

## Scope

- Проверка динамического `LLM provider` list для admin monitoring shell.
- Проверка `LLM provider`-specific page contract для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1).
- Проверка того, что UI читает backend admin read-model, а не state files напрямую.
- Проверка `LLM provider`-specific columns, drawer sections и session-scoped `Activate` semantics.
- Проверка local single-user PoC security boundary для текущего pilot scope.

## Requirement Traceability

- Requirement: admin monitoring surface строится поверх contract-first read-model и `LLM provider`-specific pages.
- Rollout metadata:
  - suite anchor: `TS-ADMIN-MONITORING-READ-MODEL`
  - future case anchors: `TC-ADMIN-MONITORING-READ-MODEL-...`
- Canonical references:
  - [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)
  - [`docs/contracts/api/admin/monitoring/providers-list.schema.json`](docs/contracts/api/admin/monitoring/providers-list.schema.json:1)
  - [`docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json:1)
  - [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- Target scripts: planned `llm_agent_platform/tests/test_admin_monitoring_read_model.py`

## Verification Command

- planned: `uv run python -m unittest llm_agent_platform/tests/test_admin_monitoring_read_model.py`

## Status

- planned

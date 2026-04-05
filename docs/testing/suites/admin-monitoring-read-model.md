# Suite: Admin monitoring read-model

## Scope

- Проверка динамического provider list для admin monitoring shell.
- Проверка provider-specific page contract для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1).
- Проверка того, что UI читает backend admin read-model, а не state files напрямую.
- Проверка provider-specific columns, drawer sections и session-scoped `Activate` semantics.
- Проверка local single-user PoC security boundary для текущего pilot scope.

## Requirement Traceability

- Requirement: admin monitoring surface строится поверх contract-first read-model и provider-specific pages.
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

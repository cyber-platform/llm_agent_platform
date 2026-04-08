# Plan: implement monitoring UI pilot for `openai-chatgpt`

## Purpose

Этот plan больше не хранит архитектурные решения.

Он фиксирует implementation order для текущего pilot UI поверх канонического SoT в `docs/`.

## Engineering SoT

Реализация обязана опираться на:

- [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)
- [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- [`docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md`](docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md:1)
- [`docs/contracts/api/admin/monitoring/providers-list.schema.json`](docs/contracts/api/admin/monitoring/providers-list.schema.json:1)
- [`docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json:1)
- [`docs/contracts/state/openai-chatgpt-usage-windows.schema.json`](docs/contracts/state/openai-chatgpt-usage-windows.schema.json:1)
- [`docs/contracts/state/openai-chatgpt-request-usage.schema.json`](docs/contracts/state/openai-chatgpt-request-usage.schema.json:1)

## Pilot scope

- один provider page: `openai-chatgpt`
- provider list строится динамически
- provider page и drawer остаются provider-specific
- local single-user PoC boundary only
- `Activate` остаётся session-scoped in-memory operator action

## Delivery slices

1. Подготовить backend admin read-model endpoints по contracts.
2. Поднять dynamic provider list в общем shell.
3. Реализовать provider-specific page для `openai-chatgpt`.
4. Реализовать grouped table с agreed pilot thresholds.
5. Реализовать provider-specific drawer.
6. Реализовать `Activate` flow без config mutation.

## Verification references

- [`docs/testing/suites/admin-monitoring-read-model.md`](docs/testing/suites/admin-monitoring-read-model.md:1)
- [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Non-goals of this plan

- не проектировать auth/RBAC в текущем PoC
- не унифицировать provider-specific page в жёсткий cross-provider UI contract
- не переносить persisted files в live frontend path

## Future work moved out

- auth/RBAC hardening: [`operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md`](operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md:1)
- monitoring UI evolution after PoC: [`operational_scope/ideas/041-monitoring-ui-future-evolution.md`](operational_scope/ideas/041-monitoring-ui-future-evolution.md:1)

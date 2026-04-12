# Materialize live refresh subsystem для admin monitoring `openai-chatgpt`

## Контекст

Архитектурный SoT для admin monitoring refresh уже зафиксирован, но backend/frontend materialization ещё отсутствует.

На текущем этапе нужно реализовать live refresh path для provider-wide monitoring страницы `openai-chatgpt`, чтобы operator UI видел актуальное состояние monitoring usage snapshots и мог запускать ручной refresh.

## Goal

Materialize backend refresh subsystem и frontend integration для provider-wide admin monitoring refresh `openai-chatgpt` в границе текущего PoC.

## Scope

В scope:

- backend provider-wide background poller для monitoring usage refresh;
- manual refresh endpoints:
  - `POST /admin/monitoring/openai-chatgpt/refresh`
  - `GET /admin/monitoring/openai-chatgpt/refresh/<refresh_id>`;
- in-memory refresh run manager с retention и duplicate-run reuse semantics;
- bounded threaded execution model;
- backend service config loading для monitoring refresh settings;
- enrichment provider page read-model по обновлённому contract schema;
- frontend short polling flow для manual refresh;
- frontend global banner / status bar / summary UX;
- tests, testing docs и suite sync для нового refresh contour.

Не входит в scope:

- SSE/WebSocket push;
- multi-provider materialization beyond `openai-chatgpt`;
- durable distributed job queue;
- admin auth/RBAC hardening.

## Canonical references

- [`docs/architecture/admin-monitoring-read-model.md`](../../docs/architecture/admin-monitoring-read-model.md)
- [`docs/architecture/admin-monitoring-refresh-subsystem.md`](../../docs/architecture/admin-monitoring-refresh-subsystem.md)
- [`docs/architecture/web-ui.md`](../../docs/architecture/web-ui.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`docs/configuration/service-behavior-config.md`](../../docs/configuration/service-behavior-config.md)
- [`docs/contracts/config/service-behavior-config.schema.json`](../../docs/contracts/config/service-behavior-config.schema.json)
- [`docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json`](../../docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json)
- [`docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-start-response.schema.json`](../../docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-start-response.schema.json)
- [`docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-status.schema.json`](../../docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-status.schema.json)
- [`docs/testing/test-map.md`](../../docs/testing/test-map.md)
- [`sot_layers/hyper-graph/docs/methodology-layer/assets/testing-system/test-map.md`](../../sot_layers/hyper-graph/docs/methodology-layer/assets/testing-system/test-map.md)
- [`sot_layers/hyper-graph/docs/methodology-layer/assets/testing-system/test-suites.md`](../../sot_layers/hyper-graph/docs/methodology-layer/assets/testing-system/test-suites.md)
- [`sot_layers/hyper-graph/docs/methodology-layer/assets/testing-system/test-case-traceability.md`](../../sot_layers/hyper-graph/docs/methodology-layer/assets/testing-system/test-case-traceability.md)

## Dependencies

- Зависит от уже materialized задач `042`, `043`, `044`, `045`, `046` как от baseline backend/frontend PoC slice.
- Является input для последующего финального doc/test sync этапа.

## Implementation notes

1. Background poller должен refresh-ить whole provider, а не selected group.
2. Manual refresh тоже должен refresh-ить whole provider.
3. Duplicate `POST /refresh` во время active run не должен создавать новый run; нужно вернуть текущий `refresh_id`.
4. Execution model: thread-based, bounded concurrency, process-local in-memory registry.
5. Config defaults:
   - `background_poll_interval_seconds = 10`
   - `refresh_concurrency = 5`
   - `per_account_refresh_timeout_seconds = 10`
   - `refresh_run_timeout_seconds = 60`
   - `refresh_run_retention_seconds = 300`
6. Provider page должна отражать отдельно:
   - routing truth (`routing.state`, `block_reason`, `quota_blocked_until`)
   - monitoring freshness (`refresh.status`, `last_refreshed_at`, `next_refresh_at`, `last_error`)
   - group-level manual refresh progress summary
7. Frontend во время manual refresh должен:
   - остановить обычный page polling;
   - short-poll `refresh status` endpoint;
   - показывать banner вида `Refreshing monitoring data 6/14`;
   - по завершении показать итоговый summary `12 refreshed, 2 failed` и вернуться к обычному polling.
8. Testing docs materialization должна следовать testing-system methodology:
   - добавить новую suite page в `docs/testing/suites/`;
   - зафиксировать `Suite ID`, `Documentation roots`, `Implementation roots`, `Search anchors`, `Test cases`;
   - обновить `docs/testing/test-map.md`;
   - test module должен иметь module docstring `Suite: TS-...`;
   - ключевые test functions должны получить docstring metadata `Test case:` и `Requirement:` там, где это уместно.

## Proposed testing slice

- Proposed suite id: `TS-ADMIN-MONITORING-REFRESH`
- Proposed implementation root: `llm_agent_platform/tests/test_admin_monitoring_refresh.py`
- Minimum coverage:
  - start manual refresh returns `202` and valid `refresh_id`;
  - repeated `POST /refresh` during active run returns same active `refresh_id`;
  - refresh status progresses from `queued/running` to terminal status;
  - `completed_with_errors` when subset of accounts fail;
  - `error` when all accounts fail;
  - provider page exposes enriched `refresh` and `supports_manual_refresh` fields;
  - frontend short polling integration or at least component/state-level smoke coverage if frontend tests are introduced.

## Definition of Done

- Backend background poller materialized and uses service behavior config.
- Manual refresh endpoints materialized and schema-compatible.
- Provider page payload updated to enriched refresh/routing semantics and remains contract-compatible.
- Frontend manual refresh UX materialized with short polling status flow.
- New refresh suite documentation added per testing-system methodology and indexed in `docs/testing/test-map.md`.
- Automated tests cover backend refresh manager, endpoint semantics and enriched read-model behavior.

## Initial status

- Current State: completed.
- Next Step: использовать materialized refresh subsystem как baseline для следующего финального PoC sync/hardening этапа.
- Blockers: none.

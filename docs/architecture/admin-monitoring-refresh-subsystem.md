# Admin Monitoring Refresh Subsystem

## Назначение

Этот документ фиксирует канонический архитектурный boundary для live refresh подсистемы admin monitoring.

Подсистема является platform-level паттерном, но в текущем PoC materialized только для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1).

Platform-wide runtime Source of Truth для monitoring memory store, hydration и persistence boundary описан в [`docs/architecture/platform-monitoring-runtime.md`](docs/architecture/platform-monitoring-runtime.md:1).

## Problem frame

Admin monitoring page должна показывать не только persisted snapshot, но и достаточно свежее состояние provider monitoring.

К текущему этапу платформа уже имеет:

- runtime routing truth в памяти процесса;
- provider-specific monitoring snapshots;
- provider-specific admin read-model page;
- локальный operator frontend, который читает только backend admin API.

Этого недостаточно для live UX, потому что routing truth и monitoring freshness могут расходиться во времени.

## Core principles

1. Backend владеет refresh lifecycle.
2. Frontend не инициирует upstream polling напрямую и не принимает backend push callbacks.
3. Routing truth и monitoring freshness являются разными слоями read-model.
4. Background polling и operator-triggered manual refresh используют один backend refresh subsystem.
5. Persisted monitoring artifacts остаются restore/audit artifacts, а не frontend delivery source.
6. Refresh subsystem обновляет memory state first и persistence second.
7. Если provider-specific monitoring даёт сильный сигнал восстановления quota, refresh subsystem может инициировать router reconciliation, но owner routing truth остаётся router.

## Read-model semantics

Provider page обязана различать:

- `routing truth`:
  - `routing.state`
  - `routing.block_reason`
  - `routing.quota_blocked_until`
- `monitoring freshness`:
  - `refresh.status`
  - `refresh.last_refreshed_at`
  - `refresh.next_refresh_at`
  - `refresh.last_error`

Следствие:

- account может уже быть `quota_blocked` или `cooldown`, даже если monitoring snapshot ещё stale;
- UI должен показывать operator truth сразу, не дожидаясь нового upstream usage snapshot.

Provider-specific note for [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1):

- successful refresh с `long_window.used_percent < 0.1` трактуется как strong evidence of long-window reset;
- refresh subsystem может после такого snapshot вызвать router reconcile path и снять persisted/in-memory quota exhaustion у account.

## Refresh scopes

Для текущего PoC зафиксированы два scope:

- background poller refreshes whole provider;
- manual refresh, вызванный оператором из UI, тоже refreshes whole provider.

Current rationale:

- page-level consistency важнее, чем partial refresh по selected group;
- provider page и provider-wide monitoring semantics остаются согласованными;
- complexity для PoC ниже, чем у mixed provider/group refresh model.

## Interaction model

### Background polling

Backend держит provider-wide background poller, который обновляет monitoring usage state через provider-specific adapter.

Current PoC cadence:

- poll interval конфигурируется через backend service config;
- default cadence для PoC: `10s`.

### Manual refresh

Кнопка `Refresh` в UI не делает synchronous long-running page reload.

Вместо этого используется lightweight async trigger:

1. frontend вызывает `POST /admin/monitoring/openai-chatgpt/refresh`;
2. backend возвращает `202 Accepted` и `refresh_id`;
3. frontend временно останавливает обычный page polling;
4. frontend делает short polling status endpoint;
5. после завершения run frontend перечитывает provider page и возвращается к обычному polling cadence.

Контракты:

- [`docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-start-response.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-start-response.schema.json:1)
- [`docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-status.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-status.schema.json:1)

## Refresh run lifecycle

Manual refresh materialize-ится как in-memory `refresh run` внутри process-local monitoring runtime.

Canonical statuses:

- `queued`
- `running`
- `completed`
- `completed_with_errors`
- `error`

Completion semantics:

- `completed` — все accounts refreshed successfully;
- `completed_with_errors` — хотя бы один account refreshed successfully и хотя бы один account failed;
- `error` — все accounts failed.

## Progress contract

Refresh status endpoint должен отдавать progress, достаточный для operator UX.

Минимальный canonical payload shape:

- `refresh_id`
- `provider_id`
- `status`
- `processed_accounts`
- `total_accounts`
- `successful_accounts`
- `failed_accounts`
- `accounts[]` c minimal per-account detail:
  - `account_name`
  - `status`
  - `last_error`

Этого достаточно для banner UX вида:

- `Refreshing monitoring data 6/14`
- `12 refreshed, 2 failed`

## Execution model

Для текущего PoC refresh subsystem использует thread-based execution inside backend process.

Canonical rationale:

- workload I/O-bound;
- backend stack остаётся sync-first;
- отдельный worker process или queue infrastructure для PoC избыточны.

Execution shape:

- один in-memory refresh manager;
- один active refresh run per provider;
- bounded concurrency через thread pool;
- refresh status registry под process-local synchronization primitive.

## Concurrency and timeouts

Operational behavior задаётся backend service config, а не `.env` secrets layer.

PoC defaults:

- `refresh_concurrency = 5`
- `per_account_refresh_timeout_seconds = 10`
- `refresh_run_timeout_seconds = 60`
- `background_poll_interval_seconds = 10`
- `refresh_run_retention_seconds = 300`

Эти значения являются PoC defaults и могут быть пересмотрены после нагрузки выше текущего масштаба.

## Duplicate manual refresh behavior

Если manual refresh уже выполняется для provider, новый `POST /refresh` не создаёт второй run.

Backend возвращает текущий active `refresh_id`.

Это предотвращает:

- дублирующий upstream polling;
- operator confusion;
- гонки между несколькими overlapping runs.

## Retention of completed runs

Completed runs хранятся в памяти ограниченное время.

Current PoC retention:

- `5 minutes`.

Rationale:

- frontend может дочитывать итог уже после завершения run;
- operator получает финальный summary без race с immediate cleanup;
- persisted job history для PoC не требуется.

## Why backend does not push into frontend

Backend-to-frontend `POST` callbacks не являются канонической delivery model.

Причины:

- browser UI не является стабильным callback server;
- trust boundary становится неестественной;
- локальный/container PoC не выигрывает от этой сложности;
- short polling status endpoint закрывает UX-задачу дешевле.

## Relation to provider-specific adapters

Refresh subsystem использует provider-specific monitoring adapters.

Для текущего PoC:

- `openai-chatgpt` refreshes только monitoring usage state;
- request-driven observability state не перезапрашивается этим subsystem и остаётся request-driven.

## Hydration relation

Persisted artifacts могут использоваться для startup hydration monitoring runtime до начала normal serving.

После startup hydration refresh subsystem больше не должен re-read persisted files как live input source для operator page.

## Current maturity and revision triggers

Текущая степень зрелости: `PoC-stage accepted architecture`.

Решение должно быть пересмотрено при одном из условий:

- multiple backend instances;
- need for durable job history or cancel semantics;
- provider count и account count заметно вырастают beyond current PoC assumptions;
- admin surface выходит за local single-user boundary.

## Related documents

- [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)
- [`docs/architecture/platform-monitoring-runtime.md`](docs/architecture/platform-monitoring-runtime.md:1)
- [`docs/configuration/service-behavior-config.md`](docs/configuration/service-behavior-config.md:1)
- [`docs/architecture/web-ui.md`](docs/architecture/web-ui.md:1)
- [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- [`docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md`](docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md:1)

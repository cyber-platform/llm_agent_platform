# Admin monitoring read-model

## Назначение

Этот документ фиксирует общий архитектурный boundary для admin monitoring surface и provider-specific monitoring pages.

Platform-wide runtime Source of Truth для monitoring storage, hydration и persistence boundary описан в [`docs/architecture/platform-monitoring-runtime.md`](docs/architecture/platform-monitoring-runtime.md:1).

Он описывает не provider-specific бизнес-семантику, а платформенные правила для:

- provider list;
- provider-specific monitoring pages;
- provider-specific drawers;
- live read path между runtime и UI;
- разграничение routing truth и monitoring freshness.

## Core principles

1. Admin UI читает только backend admin API.
2. Frontend не читает persisted state files напрямую.
3. Backend admin API строит read-model только из process-local runtime state.
4. Persisted files нужны для startup hydration, restore after restart и audit trail, но не для live UI delivery path.
5. Provider list и navigation являются общими.
6. Provider page, columns и drawer являются provider-specific.
7. Routing truth и monitoring freshness materialize-ятся отдельно.

## Provider list

Provider list появляется динамически по доступным providers.

Контракт:

- [`docs/contracts/api/admin/monitoring/providers-list.schema.json`](docs/contracts/api/admin/monitoring/providers-list.schema.json:1)

Этот endpoint даёт frontend shell минимальную навигационную модель и не фиксирует одинаковую структуру provider pages.

## Provider-specific pages

Provider page является provider-specific read-model boundary.

Это означает:

- у разных providers могут быть разные monitoring windows;
- у разных providers могут быть разные table columns;
- у разных providers могут быть разные drawer sections и raw payload fragments;
- capabilities и mutating actions могут различаться между providers.

Для текущего этапа первая provider-specific page — [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1).

Контракт текущего provider page:

- [`docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json:1)
- [`docs/contracts/api/admin/monitoring/openai-chatgpt-activate-account-response.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-activate-account-response.schema.json:1)

Для текущего PoC key-management intentionally вынесен в отдельный admin API contract set:

- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-request.schema.json`](docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-request.schema.json:1)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-response.schema.json`](docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-response.schema.json:1)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-keys-list.schema.json`](docs/contracts/api/admin/api-keys/openai-chatgpt-api-keys-list.schema.json:1)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-revoke-response.schema.json`](docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-revoke-response.schema.json:1)

## Read path

Канонический live read path:

```text
process-local monitoring runtime store -> backend admin read-model -> frontend UI
```

Неканонический и запрещённый path:

```text
state files -> frontend UI
```

## Relation to persistence

Persisted files могут временно отставать от process-local runtime state из-за async writer semantics.

Это допустимо, потому что:

- persisted files не являются live UI source;
- admin read-model строится из process-local runtime state и backend-owned refresh pipeline;
- group snapshots и provider-specific monitoring files остаются persistence artifacts, а не delivery transport.

## Routing truth vs monitoring freshness

Provider page не должна смешивать routing block state и freshness monitoring snapshots.

Canonical distinction:

- routing truth показывает, доступен ли account для selection/runtime use сейчас;
- monitoring freshness показывает, насколько свеж provider-specific usage snapshot.

Это означает, что account может быть:

- `quota_blocked` в routing layer;
- одновременно `stale` или `refreshing` в monitoring layer.

Frontend обязан показывать оба слоя без попытки свести их к одному status field.

## Refresh interaction model

Live monitoring refresh является backend-owned responsibility.

Canonical rules:

- frontend не вызывает upstream monitoring adapter напрямую;
- backend поддерживает background refresh для provider monitoring snapshots;
- operator-triggered refresh выполняется через отдельный admin action boundary;
- during manual refresh frontend short-polls refresh status endpoint и временно останавливает обычный page polling.

Подробности execution model и status lifecycle описаны в [`docs/architecture/admin-monitoring-refresh-subsystem.md`](docs/architecture/admin-monitoring-refresh-subsystem.md:1).

Текущие refresh endpoint contracts:

- [`docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-start-response.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-start-response.schema.json:1)
- [`docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-status.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-status.schema.json:1)

## Current security boundary

Для текущего мониторингового PoC admin surface больше не является no-auth contour.

Текущий baseline:

- frontend login выполняется через `services/user_service`;
- backend защищает `/admin/*` через JWT guard;
- public provider routes остаются отделены и продолжают использовать provider/public auth semantics;
- текущий auth contour intentionally lightweight и не подменяет future full RBAC hardening.

## Related documents

- [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
- [`docs/architecture/platform-monitoring-runtime.md`](docs/architecture/platform-monitoring-runtime.md:1)
- [`docs/architecture/admin-monitoring-refresh-subsystem.md`](docs/architecture/admin-monitoring-refresh-subsystem.md:1)
- [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- [`docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md`](docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md:1)

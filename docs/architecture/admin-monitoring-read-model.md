# Admin monitoring read-model

## Назначение

Этот документ фиксирует общий архитектурный boundary для admin monitoring surface.

Он описывает не provider-specific бизнес-семантику, а платформенные правила для:

- provider list;
- provider-specific monitoring pages;
- provider-specific drawers;
- live read path между runtime и UI.

## Core principles

1. Admin UI читает только backend admin API.
2. Frontend не читает persisted state files напрямую.
3. Backend admin API строит read-model из in-memory runtime state и in-memory monitoring snapshots.
4. Persisted files нужны для restore after restart и audit trail, но не для live UI delivery path.
5. Provider list и navigation являются общими.
6. Provider page, columns и drawer являются provider-specific.

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
runtime in-memory state -> backend admin read-model -> frontend UI
```

Неканонический и запрещённый path:

```text
state files -> frontend UI
```

## Relation to persistence

Persisted files могут временно отставать от in-memory state из-за async writer semantics.

Это допустимо, потому что:

- persisted files не являются live UI source;
- admin read-model строится из in-memory state;
- group snapshots и provider-specific monitoring files остаются persistence artifacts, а не delivery transport.

## Current security boundary

Для текущего мониторингового PoC no-auth admin surface допустима только как local single-user boundary.

Это ограничение относится к текущему operational scope и не должно трактоваться как общий baseline для shared dev or prod.

## Related documents

- [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
- [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- [`docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md`](docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md:1)

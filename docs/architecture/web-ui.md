# Web UI

## Назначение

Этот документ фиксирует target `Web UI` как отдельный human-facing container платформы и отделяет его от current local-only `Frontend service` PoC slice.

## Role

Target `Web UI` является единым human-facing web container поверх backend API.

## Responsibilities

- human-facing access к platform capabilities;
- navigation and interaction layer для user и admin scenarios;
- role-aware visibility через `RBAC`.

## UI composition

`Web UI` состоит из нескольких UI components и страниц.

На текущем архитектурном уровне важно зафиксировать следующие части:

- общая navigation shell;
- role-aware pages и actions;
- `LLM provider` monitoring pages;
- `LLM provider`-specific drawers и detail views.

## LLM provider-specific pages

Один из ключевых UI components — отображение лимитов использования и monitoring state для `LLM provider`.

Эта часть UI является `LLM provider`-specific, потому что:

- квоты у разных `LLM provider` учитываются по-разному;
- monitoring windows и usage semantics различаются;
- набор полей, секций и drawer content зависит от `LLM provider` semantics.

Из этого следуют два правила:

- `LLM provider` page не должна предполагать одинаковую quota model для всех `LLM provider`;
- `LLM provider`-specific monitoring pages должны строиться поверх backend read-model и `LLM provider`-specific contracts.

Каноническая архитектурная граница этого поведения описана в [`admin-monitoring-read-model.md`](./admin-monitoring-read-model.md).

## Dynamic LLM provider navigation

Страницы `LLM provider` должны появляться динамически в зависимости от того, какие `LLM provider` доступны в текущей системе.

Это означает:

- navigation для `LLM provider` pages не должна быть жёстко зашита под фиксированный `LLM provider` list;
- `LLM provider` list должен приходить из backend/admin API contract;
- `LLM provider`-specific pages должны materialize-иться поверх текущего списка доступных `LLM provider`.

## Authorization model

`Web UI` использует `RBAC` как модель role-aware visibility.

- `user` получает только read-only сценарии;
- `admin` получает configuration и administrative scenarios;
- окончательный доступ к операциям проверяет backend.

Подробности вынесены в:

- [`rbac.md`](./rbac.md)
- [`rbac-roles.md`](./rbac-roles.md)

## PoC operator UI slice

Текущий `openai-chatgpt` PoC materialize-ит не полный target `Web UI`, а отдельный operator-facing delivery slice.

Для этой PoC boundary зафиксировано:

- `Frontend service` живёт как отдельный local-only service/container;
- `Frontend service` читает только backend admin API;
- `Frontend service` не публикуется наружу;
- same-origin interaction обеспечивается через frontend-owned proxy layer;
- runtime config `Frontend service` хранится отдельно от backend service config и `.env` secrets layer.

Этот slice не отменяет target-архитектуру full `Web UI`, но является допустимым промежуточным delivery boundary для PoC.

Для current operator UX monitoring refresh используется backend-owned refresh subsystem с short polling status flow, а не browser callback/push model.

Текущие PoC contracts для этого flow:

- [`docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-start-response.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-start-response.schema.json:1)
- [`docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-status.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-status.schema.json:1)

## Status notes

- Target `Web UI` пока materialized только частично: current local-only `Frontend service` в [`services/frontend/`](services/frontend:1) покрывает operator-facing PoC slice.
- Текущая реализация покрывает `openai-chatgpt` operator page, live refresh banner/status flow, account activation и API key management.
- `LLM provider`-specific pages и dynamic `LLM provider` navigation остаются частью target architecture и должны оставаться согласованными с backend contracts при дальнейшем multi-provider расширении.

## Related documents

- container boundary: [`container-view.md`](./container-view.md)
- admin monitoring boundary: [`admin-monitoring-read-model.md`](./admin-monitoring-read-model.md)
- admin monitoring refresh: [`admin-monitoring-refresh-subsystem.md`](./admin-monitoring-refresh-subsystem.md)
- `RBAC`: [`rbac.md`](./rbac.md)
- `RBAC Roles`: [`rbac-roles.md`](./rbac-roles.md)

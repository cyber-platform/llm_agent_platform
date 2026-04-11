# Web UI

## Назначение

Этот документ фиксирует `Web UI` как отдельный human-facing container платформы.

## Role

`Web UI` является единым human-facing web container поверх runtime API.

## Responsibilities

- human-facing access к platform capabilities;
- navigation and interaction layer для user и admin scenarios;
- role-aware visibility через `RBAC`.

## UI composition

`Web UI` состоит из нескольких UI components и страниц.

На текущем архитектурном уровне важно зафиксировать следующие части:

- общая navigation shell;
- role-aware pages и actions;
- provider monitoring pages;
- provider-specific drawers и detail views.

## Provider-specific pages

Один из ключевых UI components — отображение лимитов использования и monitoring state для providers.

Эта часть UI является provider-specific, потому что:

- квоты у разных providers учитываются по-разному;
- monitoring windows и usage semantics различаются;
- набор полей, секций и drawer content зависит от provider semantics.

Из этого следуют два правила:

- provider page не должна предполагать одинаковую quota model для всех providers;
- provider-specific monitoring pages должны строиться поверх backend read-model и provider-specific contracts.

Каноническая архитектурная граница этого поведения описана в [`admin-monitoring-read-model.md`](./admin-monitoring-read-model.md).

## Dynamic provider navigation

Страницы providers должны появляться динамически в зависимости от того, какие providers доступны в текущей системе.

Это означает:

- navigation для provider pages не должна быть жёстко зашита под фиксированный provider list;
- provider list должен приходить из backend/admin API contract;
- provider-specific pages должны materialize-иться поверх текущего списка доступных providers.

## Authorization model

`Web UI` использует `RBAC` как модель role-aware visibility.

- `user` получает только read-only сценарии;
- `admin` получает configuration и administrative scenarios;
- окончательный доступ к операциям проверяет backend.

Подробности вынесены в:

- [`rbac.md`](./rbac.md)
- [`rbac-roles.md`](./rbac-roles.md)

## Status notes

- `Web UI` пока зафиксирован как target container.
- Provider-specific pages и dynamic provider navigation являются важной частью target architecture и должны оставаться согласованными с backend contracts.

## Related documents

- container boundary: [`container-view.md`](./container-view.md)
- admin monitoring boundary: [`admin-monitoring-read-model.md`](./admin-monitoring-read-model.md)
- `RBAC`: [`rbac.md`](./rbac.md)
- `RBAC Roles`: [`rbac-roles.md`](./rbac-roles.md)

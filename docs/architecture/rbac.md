# RBAC

## Назначение

Этот документ фиксирует [`RBAC`](../terms/project/terms/rbac.md) (`Role-Based Access Control`) как архитектурную модель авторизации для human-facing access к платформе.

## Scope

`RBAC` относится к:

- `Web UI` как role-aware presentation layer;
- backend-side authorization enforcement;
- источнику ролей и пользовательской identity.

Подробный состав ролей и их scope вынесен в [`rbac-roles.md`](./rbac-roles.md).

## Архитектурная роль

`RBAC` не является отдельным container.

Это cross-cutting authorization policy, которая определяет:

- какие pages и actions видит пользователь в `Web UI`;
- какие операции backend разрешает выполнять;
- как role assignment влияет на human-facing сценарии платформы.

## Enforcement boundary

Разделение ответственности:

- `Web UI` отвечает за role-aware navigation, visibility и interaction gating;
- backend отвечает за итоговую authorization enforcement для операций;
- роль пользователя не должна считаться защищённой только потому, что UI не показал кнопку или страницу.

Это означает, что `Web UI` является display layer, а не authoritative security boundary.

## Role source

Источник ролей и пользовательской identity пока фиксируется как staged architecture.

### Ранний этап

- backend обращается напрямую к `users DB`;
- `users DB` хранит user records и role assignment;
- отдельный `user service` ещё не обязателен.

### Целевой этап

- backend обращается к `user service`;
- `user service` владеет авторизацией пользователя и доступом к пользовательским данным;
- `users DB` остаётся persistence boundary за `user service`.

## Current freeze

На текущем этапе можно считать зафиксированным следующее:

- `Web UI` использует `RBAC`;
- backend является authorization enforcement boundary;
- роли определяют набор доступных pages и actions;
- роли `user` и `admin` описываются в [`rbac-roles.md`](./rbac-roles.md).

## Open questions

- где именно materialize-ится authoritative login/session boundary;
- будет ли `user service` отдельным runtime service или ранний этап останется на direct backend to users DB path;
- как будет устроен lifecycle role changes и session refresh.

## Related documents

- container boundary: [`container-view.md`](./container-view.md)
- admin monitoring boundary: [`admin-monitoring-read-model.md`](./admin-monitoring-read-model.md)
- roles and scopes: [`rbac-roles.md`](./rbac-roles.md)

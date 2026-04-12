# RBAC

## Назначение термина

`RBAC` (`Role-Based Access Control`) — модель авторизации, в которой доступ к страницам, действиям и операциям определяется ролью пользователя.

## Роль в проекте

В `llm_agent_platform` `RBAC` используется как human-facing authorization model для `Web UI` и связанных backend-side authorization checks.

Эта модель определяет:

- какие pages и actions видит пользователь;
- какие сценарии доступны роли `user`;
- какие сценарии доступны роли `admin`.

## Связанные документы

- [`terms-map.md`](../terms-map.md)
- [`rbac.md`](../../../architecture/rbac.md)
- [`rbac-roles.md`](../../../architecture/rbac-roles.md)

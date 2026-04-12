# RBAC Roles

## Назначение

Этот документ фиксирует роли `RBAC` и их scope возможностей для human-facing access к платформе.

Общая модель `RBAC` описана в [`rbac.md`](./rbac.md).

## Roles

### `user`

- Status: current baseline role.
- Scope:
  - read-only access;
  - просмотр доступных страниц, статусов и данных, которые backend разрешает читать;
  - без platform configuration и administrative mutations.

### `admin`

- Status: current administrative role.
- Scope:
  - platform configuration;
  - administrative actions;
  - access к admin/monitoring/configuration scenarios, разрешённым backend.

## Policy note

- `Web UI` может скрывать или показывать pages и actions по роли;
- окончательное разрешение операции должен проверять backend.

## Open questions

- какие именно configuration actions войдут в первый freeze admin scope;
- будет ли нужен дополнительный split внутри administrative roles на более позднем этапе.

## Related documents

- `RBAC`: [`rbac.md`](./rbac.md)
- container boundary: [`container-view.md`](./container-view.md)

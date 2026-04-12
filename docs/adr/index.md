# ADR Index

## Назначение

Этот индекс является entry point для long-lived architecture decisions проекта.

ADR фиксируют rationale, alternatives и consequences решений, которые уже стали частью engineering knowledge.

## ADR catalog

- [`0014-stream-state-container-and-429-rotation-policy.md`](./0014-stream-state-container-and-429-rotation-policy.md)
- [`0015-env-separation-runtime-vs-oauth-bootstrap.md`](./0015-env-separation-runtime-vs-oauth-bootstrap.md)
- [`0016-codebase-layout-separate-runtime-app-and-local-scripts.md`](./0016-codebase-layout-separate-runtime-app-and-local-scripts.md)
- [`0017-url-prefix-groups-and-group-aware-models.md`](./0017-url-prefix-groups-and-group-aware-models.md)
- [`0018-quota-reset-periods-and-account-state.md`](./0018-quota-reset-periods-and-account-state.md)
- [`0019-state-dir-unified-account-state-and-async-writer.md`](./0019-state-dir-unified-account-state-and-async-writer.md)
- [`0020-provider-centric-routing-and-provider-catalogs.md`](./0020-provider-centric-routing-and-provider-catalogs.md)
- [`0021-account-centric-provider-monitoring-and-admin-read-model.md`](./0021-account-centric-provider-monitoring-and-admin-read-model.md)
- [`0022-admin-monitoring-live-refresh-subsystem.md`](./0022-admin-monitoring-live-refresh-subsystem.md)
- [`0023-monitoring-refresh-threaded-execution-model.md`](./0023-monitoring-refresh-threaded-execution-model.md)
- [`0024-poc-operator-frontend-delivery-boundary.md`](./0024-poc-operator-frontend-delivery-boundary.md)

## Как читать

- Для текущего system framing начинать с [`0020-provider-centric-routing-and-provider-catalogs.md`](./0020-provider-centric-routing-and-provider-catalogs.md).
- Для state persistence и monitoring boundaries идти в [`0019-state-dir-unified-account-state-and-async-writer.md`](./0019-state-dir-unified-account-state-and-async-writer.md), [`0021-account-centric-provider-monitoring-and-admin-read-model.md`](./0021-account-centric-provider-monitoring-and-admin-read-model.md), [`0022-admin-monitoring-live-refresh-subsystem.md`](./0022-admin-monitoring-live-refresh-subsystem.md).
- Для frontend delivery boundary смотреть [`0024-poc-operator-frontend-delivery-boundary.md`](./0024-poc-operator-frontend-delivery-boundary.md).

## Related documents

- architecture index: [`index.md`](../architecture/index.md)
- contracts index: [`index.md`](../contracts/index.md)

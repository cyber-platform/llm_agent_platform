# Services Index

## Назначение

Этот документ фиксирует service topology системы `llm_agent_platform`.

Он нужен, чтобы отделить system-level architecture от service-local implementation context и явно показать repo boundaries между сервисами.

## Service model

`llm_agent_platform` является одной системой, которая materialize-ится как набор автономных services.

Технологический стек проекта оркестрируется через [`HSM`](../terms/project/terms/hsm.md).

## Карта сервисов

| Service | Роль | Repository boundary | Status |
| --- | --- | --- | --- |
| Frontend service | Local-only operator/admin frontend service, materializing current `Web UI` slice. | local path [`services/frontend/`](../../services/frontend), GitHub: [frontend repo](https://github.com/cyber-platform/frontend.git) | active nested repo |
| Backend service | Machine-facing provider API и admin-facing backend runtime. | target local path `services/backend/`, GitHub repo публикуется отдельно | planned split |

## Repo ownership

- Root repo владеет system-level documentation, integration framing и local stack materialization artifacts.
- `Frontend service` и `Backend service` владеют своим implementation code, service-local runtime details и service-local developer workflow.
- Root `docs/` не должен дублировать service-internal code documentation; он фиксирует system boundaries, contracts и integration semantics.

## Service relations

- `Frontend service` ходит только в `Backend service`.
- `Backend service` владеет provider integrations, runtime auth, routing, quota semantics и admin API.
- Local multi-service delivery может materialize-иться через root-level `docker-compose`, но это не меняет service boundaries.

## Related documents

- root documentation map: [`index.md`](../index.md)
- system context: [`system-overview.md`](../architecture/system-overview.md)
- container topology: [`container-view.md`](../architecture/container-view.md)
- `HSM`: [`hsm`](../terms/project/terms/hsm.md)

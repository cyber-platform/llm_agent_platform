# Service-wide health-check endpoints для `backend`, `frontend` и `user_service`

## Контекст

В `PoC2` зафиксирован быстрый operational baseline, в котором все runtime services должны иметь простой и проверяемый health contour.

Для текущей assembled системы это минимум:

- `services/backend`;
- `services/frontend`;
- `services/user_service`.

Health-check нужен как для локальной сборки, так и для дальнейшего monitoring/deploy contour.

## Goal

Материализовать согласованные `health-check` endpoints или эквивалентные container health probes для всех runtime services текущего `PoC2` контура.

## Scope

В scope:

- `health-check` для `services/backend`;
- проверка и при необходимости нормализация `health-check` для `services/frontend`;
- проверка и при необходимости нормализация `health-check` для `services/user_service`;
- синхронизация локального compose/runtime contour, если это требуется для health probing;
- минимальная verification фиксация.

Не входит в scope:

- readiness/liveness split с production-grade semantics;
- deep observability stack;
- auth/RBAC changes;
- расширенные runtime dependency checks beyond простого baseline.

## Canonical references

- [`operational_scope/plans/poc2/poc2-priority-implementation-plan.md`](../plans/poc2/poc2-priority-implementation-plan.md)
- [`operational_scope/plans/poc2/poc2.md`](../plans/poc2/poc2.md)
- [`docs/architecture/component-map.md`](../../docs/architecture/component-map.md)
- [`docs/vision.md`](../../docs/vision.md)
- [`services/backend/llm_agent_platform/__main__.py`](../../services/backend/llm_agent_platform/__main__.py)
- [`services/frontend/nginx.conf`](../../services/frontend/nginx.conf)
- [`services/user_service/app/main.py`](../../services/user_service/app/main.py)

## Dependencies

- Архитектурных blockers нет.
- Может выполняться независимо от auth/login задач.
- Является ранней operational dependency для `Prometheus`/`Grafana` контура и для дальнейшей verification automation.

## Implementation notes

1. Для `services/backend` нужен явный `/health`, так как это критичная runtime boundary.
2. Для `services/frontend` допустим легкий `nginx`/container health contour, если он остается проверяемым и стабильным.
3. Для `services/user_service` нужно использовать существующий endpoint или привести его к согласованной форме.
4. Не нужно превращать health endpoint в тяжелую self-diagnostics subsystem.

## Definition of Done

- У всех трех сервисов есть проверяемый health contour.
- `services/backend` отдает явный `health-check` endpoint.
- `services/frontend` и `services/user_service` имеют рабочий и документируемый способ health probing.
- Если нужны изменения в compose/runtime assembly, они materialized.
- Есть минимальный verification trail с примерами проверки.

## Initial status

- Current State: planned.
- Next Step: выполнить task как первый технический шаг Priority 1.
- Blockers: none.

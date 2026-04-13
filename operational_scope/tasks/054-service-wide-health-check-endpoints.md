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

## Execution notes

- `services/backend` получил явный `GET /health` с легким JSON payload `{"status": "ok", "service": "backend"}`.
- `services/frontend` нормализован через `nginx` endpoint `GET /health` и compose-level probe для root delivery contour.
- `services/user_service` сохранил существующий `GET /health`; для `dev` и `prod` compose добавлен явный container healthcheck.
- Минимальный verification trail зафиксирован в [`docs/testing/suites/service-health-checks.md`](../../docs/testing/suites/service-health-checks.md) и backend suite [`services/backend/llm_agent_platform/tests/test_service_health_checks.py`](../../services/backend/llm_agent_platform/tests/test_service_health_checks.py).

## Materialized changes

- В [`services/backend/llm_agent_platform/__main__.py`](../../services/backend/llm_agent_platform/__main__.py) добавлен route-level health endpoint без привязки к auth, monitoring refresh или provider-specific runtime.
- В [`services/frontend/nginx.conf`](../../services/frontend/nginx.conf) добавлен standalone `location = /health`, возвращающий статический JSON, чтобы frontend health probe не зависел от SPA bundle или backend proxy.
- В [`docker-compose.yml`](../../docker-compose.yml) и [`docker-compose-dev.yml`](../../docker-compose-dev.yml) добавлены `healthcheck` секции для `backend` и `frontend`; backend probe использует Python stdlib request к `http://127.0.0.1:4000/health`, frontend probe использует `wget` к `http://127.0.0.1/health`.
- В [`services/user_service/docker-compose-dev.yml`](../../services/user_service/docker-compose-dev.yml) и [`services/user_service/docker-compose-prod.yml`](../../services/user_service/docker-compose-prod.yml) добавлены `healthcheck` секции для API-контейнера поверх существующего endpoint `http://127.0.0.1:8000/health`.
- В [`services/backend/llm_agent_platform/tests/test_service_health_checks.py`](../../services/backend/llm_agent_platform/tests/test_service_health_checks.py) добавлен suite `TS-SERVICE-HEALTH-CHECKS`, который проверяет backend endpoint contract и checked-in probe wiring для frontend и `user_service`.
- В [`docs/testing/suites/service-health-checks.md`](../../docs/testing/suites/service-health-checks.md) создана suite page; в [`docs/testing/test-map.md`](../../docs/testing/test-map.md) добавлен индекс этого verification contour.
- В [`services/user_service/docker-compose-prod.yml`](../../services/user_service/docker-compose-prod.yml) одновременно удален obsolete `version` field после compose validation warning, чтобы checked-in prod compose оставался clean.

## Verification trail

- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_service_health_checks.py` -> `OK`.
- `docker compose -f docker-compose.yml config` -> `OK`.
- `docker compose -f docker-compose-dev.yml config` -> `OK`.
- `cd services/user_service && docker compose -f docker-compose-dev.yml config` -> `OK`.
- `cd services/user_service && docker compose -f docker-compose-prod.yml config` -> `OK`.

## Handoff context

- Task закрыт как completed; активный backlog в [`operational_scope/tasks_map.md`](../tasks_map.md) больше не содержит задачу `054`.
- Получившийся baseline intentionally lightweight: это только cheap health contour для локальной сборки и дальнейшего monitoring/deploy слоя, без readiness/liveness split и без deep dependency diagnostics.
- Следующие PoC2 задачи могут безопасно опираться на наличие стабильных probes у всех трех runtime services.

## Final status

- Current State: completed.
- Verification: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_service_health_checks.py`
- Blockers: none.

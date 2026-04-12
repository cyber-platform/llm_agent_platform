# Service Health Checks

## Suite ID
- `TS-SERVICE-HEALTH-CHECKS`

## Scope
- backend `/health` contract for the Flask runtime shell;
- frontend `nginx` health endpoint and compose probe wiring;
- `user_service` `/health` baseline and compose probe wiring.

## Documentation roots
- [`operational_scope/tasks/054-service-wide-health-check-endpoints.md`](../../../operational_scope/tasks/054-service-wide-health-check-endpoints.md)
- [`docs/architecture/component-map.md`](../../architecture/component-map.md)

## Implementation roots
- [`services/backend/llm_agent_platform/tests/test_service_health_checks.py`](../../../services/backend/llm_agent_platform/tests/test_service_health_checks.py)
- [`services/backend/llm_agent_platform/__main__.py`](../../../services/backend/llm_agent_platform/__main__.py)
- [`services/frontend/nginx.conf`](../../../services/frontend/nginx.conf)
- [`docker-compose.yml`](../../../docker-compose.yml)
- [`docker-compose-dev.yml`](../../../docker-compose-dev.yml)
- [`services/user_service/app/main.py`](../../../services/user_service/app/main.py)
- [`services/user_service/docker-compose-dev.yml`](../../../services/user_service/docker-compose-dev.yml)
- [`services/user_service/docker-compose-prod.yml`](../../../services/user_service/docker-compose-prod.yml)

## Search anchors
- `TS-SERVICE-HEALTH-CHECKS`
- `TC-SERVICE-HEALTH-CHECKS`
- `/health`
- `healthcheck:`

## Verification
- Backend suite: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_service_health_checks.py`
- Local compose probe examples:
  - `curl http://127.0.0.1:4000/health`
  - `curl http://127.0.0.1:4173/health`
  - `curl http://127.0.0.1:8010/health`

# Test Map

## Overview
- Контур покрывает `LLM provider`-centric OpenAI-compatible контракт, quota-runtime поведение и `LLM provider`-specific boundaries.
- Целевая трассировка: `requirement -> suite -> test case -> test implementation`.
- Текущее состояние rollout: suite-level `TS-*` идентификаторы уже каноничны; test-case-level `TC-*` вводятся постепенно по мере обновления suites и test code.

## Conventions
- Testing documentation SoT живет в `docs/testing/`.
- Каждая suite page должна задавать `Suite ID`, `Documentation roots`, `Implementation roots` и `Search anchors`.
- Если агенту нужна документация по suite, search нужно начинать в `docs/testing/`.
- Если агенту нужна реализация тестов, search нужно начинать с `Implementation roots`, указанных в suite page.
- Подробные traceability conventions зафиксированы в `docs/testing/traceability.md`.

## Suites
| Suite ID | Suite Page | Scope | Implementation roots | Status |
| :--- | :--- | :--- | :--- | :--- |
| `TS-OPENAI-CONTRACT` | [`openai-contract.md`](docs/testing/suites/openai-contract.md) | OpenAI stream/non-stream contract, `LLM provider`-scoped routes, `openai-chatgpt` provider implementation and streamed error mapping | [`services/backend/llm_agent_platform/tests/test_openai_contract.py`](services/backend/llm_agent_platform/tests/test_openai_contract.py:1), [`services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py`](services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1) | active |
| `TS-PROXY-ROUTES` | [`proxy-routes.md`](docs/testing/suites/proxy-routes.md) | `LLM provider`-scoped routing, group-aware routes, native Gemini proxy and parity relay coverage | [`services/backend/llm_agent_platform/tests/test_refactor_p2_routes.py`](services/backend/llm_agent_platform/tests/test_refactor_p2_routes.py:1) | active |
| `TS-PROVIDER-CATALOGS` | [`provider-catalogs.md`](docs/testing/suites/provider-catalogs.md) | `LLM provider`-local catalogs and static bootstrap catalog boundaries | [`services/backend/llm_agent_platform/tests/test_provider_catalogs.py`](services/backend/llm_agent_platform/tests/test_provider_catalogs.py:1) | active |
| `TS-QUOTA-PARITY` | [`quota-parity.md`](docs/testing/suites/quota-parity.md) | Quota transport parity with `gemini-cli` payload and stream shape | [`services/backend/llm_agent_platform/tests/test_quota_transport_parity.py`](services/backend/llm_agent_platform/tests/test_quota_transport_parity.py:1) | active |
| `TS-QUOTA-ACCOUNT-ROTATION` | [`quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md) | Unified quota rotation, group isolation, `LLM provider`-scoped models and cooldown fast-fail behavior | [`services/backend/llm_agent_platform/tests/test_quota_account_router.py`](services/backend/llm_agent_platform/tests/test_quota_account_router.py:1), [`services/backend/llm_agent_platform/tests/test_refactor_p2_routes.py`](services/backend/llm_agent_platform/tests/test_refactor_p2_routes.py:1), [`services/backend/llm_agent_platform/tests/test_openai_contract.py`](services/backend/llm_agent_platform/tests/test_openai_contract.py:1) | active |
| `TS-QUOTA-STATE-PERSISTENCE` | [`quota-state-persistence.md`](docs/testing/suites/quota-state-persistence.md) | Persisted quota state, `STATE_DIR`, `LLM provider`-specific artifacts, group snapshot and async writer | [`services/backend/llm_agent_platform/tests/test_quota_account_router.py`](services/backend/llm_agent_platform/tests/test_quota_account_router.py:1) | active |
| `TS-ADMIN-API-KEYS` | [`admin-api-keys.md`](docs/testing/suites/admin-api-keys.md) | Provider-scoped API key registry, hash-only storage and admin CRUD for `openai-chatgpt` platform keys | [`services/backend/llm_agent_platform/tests/test_admin_api_keys.py`](services/backend/llm_agent_platform/tests/test_admin_api_keys.py:1) | active |
| `TS-OPENAI-CHATGPT-REQUEST-POLICIES` | [`openai-chatgpt-request-policies.md`](docs/testing/suites/openai-chatgpt-request-policies.md) | Key-scoped request policy registry service, no-policy read semantics and capability-backed validation for `openai-chatgpt` | [`services/backend/llm_agent_platform/tests/test_openai_chatgpt_request_policies.py`](services/backend/llm_agent_platform/tests/test_openai_chatgpt_request_policies.py:1) | active |
| `TS-ADMIN-JWT-GUARD` | [`admin-jwt-guard.md`](docs/testing/suites/admin-jwt-guard.md) | JWT guard for `/admin/*`, `developer -> admin` mapping and predictable unauthorized responses for `PoC2` | [`services/backend/llm_agent_platform/tests/test_admin_auth_guard.py`](services/backend/llm_agent_platform/tests/test_admin_auth_guard.py:1) | active |
| `TS-ADMIN-MONITORING-READ-MODEL` | [`admin-monitoring-read-model.md`](docs/testing/suites/admin-monitoring-read-model.md) | Dynamic `LLM provider` list, `LLM provider`-specific monitoring page and backend read-model boundary | [`services/backend/llm_agent_platform/tests/test_admin_monitoring_read_model.py`](services/backend/llm_agent_platform/tests/test_admin_monitoring_read_model.py:1) | active |
| `TS-ADMIN-MONITORING-REFRESH` | [`admin-monitoring-refresh.md`](docs/testing/suites/admin-monitoring-refresh.md) | Provider-wide monitoring refresh manager, manual refresh endpoints and operator progress contract for `openai-chatgpt` | [`services/backend/llm_agent_platform/tests/test_admin_monitoring_refresh.py`](services/backend/llm_agent_platform/tests/test_admin_monitoring_refresh.py:1) | active |
| `TS-OPENAI-CHATGPT-POC-SMOKE` | [`openai-chatgpt-poc-smoke.md`](docs/testing/suites/openai-chatgpt-poc-smoke.md) | Final PoC smoke contour across key lifecycle, monitoring payload compatibility and checked-in local/public delivery boundary | [`services/backend/llm_agent_platform/tests/test_openai_chatgpt_poc_smoke.py`](services/backend/llm_agent_platform/tests/test_openai_chatgpt_poc_smoke.py:1), `services/frontend` build smoke | active |
| `TS-SERVICE-HEALTH-CHECKS` | [`service-health-checks.md`](docs/testing/suites/service-health-checks.md) | Service-wide `/health` and compose probe contour for `backend`, `frontend` and `user_service` | [`services/backend/llm_agent_platform/tests/test_service_health_checks.py`](services/backend/llm_agent_platform/tests/test_service_health_checks.py:1) | active |
| `TS-USER-SERVICE-PLATFORM-AUTH` | [`user-service-platform-auth.md`](docs/testing/suites/user-service-platform-auth.md) | `user_service` login/JWT baseline, role claims and checked-in shared-secret wiring for `PoC2` | [`services/user_service/tests/test_auth_baseline.py`](services/user_service/tests/test_auth_baseline.py:1) | active |
| `TS-CONFIG-ENV-AND-LAYOUT` | [`config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md) | Env split, runtime package layout and verification command alignment | manual + smoke scripts | planned |

## Runbook
- Запуск: `cd services/backend && uv run python -m unittest discover -s llm_agent_platform/tests -p "test_*.py"`
- Быстрая проверка синтаксиса: `cd services/backend && uv run python -m compileall llm_agent_platform`
- Тестовые артефакты: используются фиктивные файлы в `secrets_test/`
- Целевая проверка admin API keys: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_api_keys.py`
- Целевая проверка request policy registry: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_request_policies.py`
- Целевая проверка admin JWT guard: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_auth_guard.py`
- Целевая проверка admin monitoring read-model: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_monitoring_read_model.py`
- Целевая проверка admin monitoring refresh: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_monitoring_refresh.py`
- Целевая runtime-проверка `openai-chatgpt`: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_runtime.py`
- Целевая проверка service health contour: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_service_health_checks.py`
- Целевая проверка `user_service` auth baseline: `cd services/user_service && uv run pytest tests/test_auth_baseline.py`
- Финальный PoC smoke contour: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_poc_smoke.py`
- Frontend build smoke для текущего PoC: `npm run build` (из `services/frontend`)

## Related Files
- `docs/testing/traceability.md`
- `docs/testing/suites/`

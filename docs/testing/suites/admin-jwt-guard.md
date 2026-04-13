# Suite: Admin JWT guard

## Suite ID
- `TS-ADMIN-JWT-GUARD`

## Documentation roots
- `docs/testing/test-map.md`
- `docs/testing/traceability.md`
- `docs/testing/suites/admin-jwt-guard.md`

## Implementation roots
- `services/backend/llm_agent_platform/tests/test_admin_auth_guard.py`

## Search anchors
- `TS-ADMIN-JWT-GUARD`
- `test_admin_auth_guard.py`
- `admin jwt guard`
- `developer -> admin`

## Scope
- Проверка того, что `/admin/*` требует Bearer JWT из `user_service` shared-secret контура.
- Проверка backend-owned mapping `developer -> admin` только внутри admin guard.
- Проверка предсказуемых negative responses для missing bearer token и insufficient role.
- Проверка того, что auth guard можно тестировать изолированно от admin service implementations.

## Requirement Traceability
- Requirement: backend admin surface отделяется от public provider auth boundary и защищается JWT quick baseline для `PoC2`.
- Rollout metadata:
  - suite anchor: `TS-ADMIN-JWT-GUARD`
  - case anchors: `TC-ADMIN-JWT-GUARD-001..003`
- Canonical references:
  - [`docs/auth.md`](docs/auth.md:252)
  - [`operational_scope/tasks/056-backend-admin-jwt-guard-via-user-service.md`](operational_scope/tasks/056-backend-admin-jwt-guard-via-user-service.md:1)
  - [`services/backend/llm_agent_platform/api/admin/auth_guard.py`](services/backend/llm_agent_platform/api/admin/auth_guard.py:1)
  - [`services/backend/llm_agent_platform/api/admin/routes.py`](services/backend/llm_agent_platform/api/admin/routes.py:1)

## Verification Command
- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_auth_guard.py`

## Status
- active

# User Service Platform Auth

## Suite ID
- `TS-USER-SERVICE-PLATFORM-AUTH`

## Scope
- `user_service` shared-secret auth baseline for current `PoC2`;
- JWT claim shape needed for backend `developer -> admin` mapping;
- checked-in compose/env wiring for `JWT_SHARED_SECRET`.

## Documentation roots
- [`operational_scope/tasks/055-user-service-platform-auth-baseline.md`](../../../operational_scope/tasks/055-user-service-platform-auth-baseline.md)
- [`docs/auth.md`](../../auth.md)

## Implementation roots
- [`services/user_service/app/api/auth.py`](../../../services/user_service/app/api/auth.py)
- [`services/user_service/app/core/config.py`](../../../services/user_service/app/core/config.py)
- [`services/user_service/app/core/security.py`](../../../services/user_service/app/core/security.py)
- [`services/user_service/tests/test_auth_baseline.py`](../../../services/user_service/tests/test_auth_baseline.py)
- [`services/user_service/docker-compose-dev.yml`](../../../services/user_service/docker-compose-dev.yml)
- [`services/user_service/docker-compose-prod.yml`](../../../services/user_service/docker-compose-prod.yml)

## Search anchors
- `TS-USER-SERVICE-PLATFORM-AUTH`
- `TC-USER-SERVICE-PLATFORM-AUTH`
- `JWT_SHARED_SECRET`
- `build_access_token_claims`

## Verification
- `cd services/user_service && uv run pytest tests/test_auth_baseline.py`
- `cd services/user_service && docker compose -f docker-compose-dev.yml config`
- `cd services/user_service && docker compose -f docker-compose-prod.yml config`

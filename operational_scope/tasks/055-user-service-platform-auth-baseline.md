# Адаптация `user_service` под platform auth baseline для `PoC2`

## Контекст

Для Priority 1 в `PoC2` зафиксирован быстрый auth baseline:

- `services/user_service` остается identity boundary;
- `services/backend` валидирует JWT через shared secret;
- роль `developer` трактуется как `admin` для operator/admin surface;
- отдельный `observer` role пока не вводится.

Существующий `user_service` пришел из другого проекта и должен быть адаптирован под текущую assembled систему без переноса лишнего доменного поведения.

## Goal

Подготовить `services/user_service` как минимально достаточный identity service для `PoC2`, совместимый с login flow, shared-secret JWT verification и role mapping текущей платформы.

## Scope

В scope:

- проверка и адаптация login/JWT baseline под текущую платформу;
- явная фиксация shared JWT secret integration path;
- сохранение и reuse existing brute-force protection;
- проверка role payload/claims, достаточных для admin surface;
- удаление или изоляция лишних для `PoC2` зависимостей, если они мешают текущему auth contour;
- minimal docs/config sync, если это требуется для запуска.

Не входит в scope:

- полноценный RBAC redesign;
- audit trail;
- refresh-token flow;
- production-grade IAM design;
- переработка `user_service` во всеобщий account platform.

## Canonical references

- [`operational_scope/plans/poc2/poc2-priority-implementation-plan.md`](../plans/poc2/poc2-priority-implementation-plan.md)
- [`operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md`](../plans/040-admin-surface-auth-and-rbac-hardening.md)
- [`docs/auth.md`](../../docs/auth.md)
- [`services/user_service/app/api/auth.py`](../../services/user_service/app/api/auth.py)
- [`services/user_service/app/models/user.py`](../../services/user_service/app/models/user.py)
- [`services/user_service/docs/brute_force_protection.md`](../../services/user_service/docs/brute_force_protection.md)

## Dependencies

- Опирается на freeze decisions из `poc2-priority-implementation-plan.md`.
- Является dependency для backend admin JWT guard.
- Является dependency для frontend login flow.

## Implementation notes

1. Нельзя silently расширять auth semantics beyond agreed quick baseline.
2. JWT claims должны быть достаточны для backend role mapping.
3. Если в `user_service` есть лишние для `PoC2` части, их не нужно обязательно удалять, достаточно не тащить их в critical path.
4. Нужно сохранить совместимость с будущим hardening plan и не выдавать quick baseline за финальную security architecture.

## Definition of Done

- `services/user_service` стабильно поддерживает login/JWT flow для текущей platform assembly.
- Shared secret integration path явно materialized и проверяем.
- Role/claims достаточны для `developer -> admin` mapping на backend.
- Brute-force protection не теряется.
- Есть verification notes для login и JWT issuance path.

## Execution notes

- `services/user_service` сохранил existing `/auth/login` route и brute-force behavior, но теперь выдает JWT с явными platform claims для backend admin guard baseline.
- Shared-secret integration path materialized через `JWT_SHARED_SECRET`; при этом сохранен временный fallback на legacy `SECRET_KEY`, чтобы не ломать текущий локальный contour.
- JWT payload нормализован до минимального набора `sub`, `user_id`, `role`, `roles`, `iss`, `iat`, `exp` без переноса future hardening semantics в `PoC2` baseline.
- Login response теперь возвращает `role`, чтобы frontend/login shell мог синхронизировать локальный auth state без дополнительного profile roundtrip.

## Materialized changes

- В [`services/user_service/app/core/config.py`](../../services/user_service/app/core/config.py) введен явный settings path `JWT_SHARED_SECRET` с backward-compatible fallback на `SECRET_KEY` и issuer baseline `user_service`.
- В [`services/user_service/app/core/security.py`](../../services/user_service/app/core/security.py) JWT signing переведен на shared-secret settings path; токены теперь получают `iss` и `iat` вместе с `exp`.
- В [`services/user_service/app/api/auth.py`](../../services/user_service/app/api/auth.py) добавлен helper `build_access_token_claims()` и login payload/response с `role` и `roles[]` claims.
- В [`services/user_service/docker-compose-dev.yml`](../../services/user_service/docker-compose-dev.yml), [`services/user_service/docker-compose-prod.yml`](../../services/user_service/docker-compose-prod.yml) и [`services/user_service/.env.example`](../../services/user_service/.env.example) checked-in env wiring переведено на `JWT_SHARED_SECRET`.
- В [`services/user_service/tests/test_auth_baseline.py`](../../services/user_service/tests/test_auth_baseline.py) добавлен suite `TS-USER-SERVICE-PLATFORM-AUTH` для settings alias, role-claims и JWT issuance baseline.
- В [`docs/auth.md`](../../docs/auth.md), [`docs/testing/suites/user-service-platform-auth.md`](../../docs/testing/suites/user-service-platform-auth.md) и [`docs/testing/test-map.md`](../../docs/testing/test-map.md) зафиксированы canonical verification notes для текущего auth contour.

## Verification trail

- `cd services/user_service && uv run pytest tests/test_auth_baseline.py`
- `cd services/user_service && docker compose -f docker-compose-dev.yml config`
- `cd services/user_service && docker compose -f docker-compose-prod.yml config`

## Handoff context

- Task закрывает dependency для backend admin JWT guard и frontend login flow, не вводя refresh tokens, introspection endpoint или separate `observer` role.
- Backend должен трактовать `developer` как `admin` внутри собственного `/admin/*` guard; это mapping остается backend-owned semantics.
- Future hardening и полноформатный RBAC по-прежнему вынесены в [`operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md`](../plans/040-admin-surface-auth-and-rbac-hardening.md).
- Следующий агент может опираться на то, что canonical shared-secret env name уже зафиксирован как `JWT_SHARED_SECRET`, а legacy `SECRET_KEY` оставлен только как compatibility fallback в `user_service`.
- Checked-in test coverage для этого baseline живет в [`services/user_service/tests/test_auth_baseline.py`](../../services/user_service/tests/test_auth_baseline.py) и покрывает alias env, claim shape и JWT decode path c issuer verification.
- Compose validation для `services/user_service` уже выполнена после перевода env wiring на `JWT_SHARED_SECRET`; additional compose changes для этой задачи не требуются.
- При verification были замечены только существующие deprecation warnings из [`services/user_service/app/db/base.py`](../../services/user_service/app/db/base.py) и [`services/user_service/app/schemas/user.py`](../../services/user_service/app/schemas/user.py); они не блокируют текущий auth baseline.

## Final status

- Current State: completed.
- Verification: `cd services/user_service && uv run pytest tests/test_auth_baseline.py`
- Blockers: none.

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

## Initial status

- Current State: planned.
- Next Step: materialize auth baseline для dependency chain `user_service -> backend -> frontend`.
- Blockers: none.

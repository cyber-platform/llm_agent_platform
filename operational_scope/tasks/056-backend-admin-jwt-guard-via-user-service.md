# Backend admin JWT guard через `user_service` shared-secret baseline

## Контекст

Текущий admin surface backend intentionally оставался no-auth local PoC boundary.

Для `PoC2` зафиксирован быстрый переход к минимальному auth contour:

- JWT приходит из `services/user_service`;
- `services/backend` валидирует JWT через shared secret;
- JWT auth применяется только к `/admin/*`;
- public OpenAI-compatible provider routes сохраняют platform API key auth;
- `developer` трактуется как `admin`.

## Goal

Защитить backend admin surface через JWT guard, не смешивая admin auth boundary с public provider auth boundary.

## Scope

В scope:

- JWT verification middleware/guard для `/admin/*`;
- role mapping `developer -> admin`;
- отказ в доступе для non-admin path текущего быстрого контура;
- сохранение существующего platform API key auth для public provider routes;
- negative/positive tests для admin auth path.

Не входит в scope:

- auth для public provider routes;
- полноценный `observer/admin` RBAC;
- audit logging;
- refresh-token flow;
- auth hardening beyond current quick baseline.

## Canonical references

- [`operational_scope/plans/poc2/poc2-priority-implementation-plan.md`](../plans/poc2/poc2-priority-implementation-plan.md)
- [`operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md`](../plans/040-admin-surface-auth-and-rbac-hardening.md)
- [`docs/auth.md`](../../docs/auth.md)
- [`docs/architecture/admin-monitoring-read-model.md`](../../docs/architecture/admin-monitoring-read-model.md)
- [`services/backend/llm_agent_platform/api/admin/routes.py`](../../services/backend/llm_agent_platform/api/admin/routes.py)
- [`services/backend/llm_agent_platform/api/openai/auth_guard.py`](../../services/backend/llm_agent_platform/api/openai/auth_guard.py)

## Dependencies

- Зависит от [`055-user-service-platform-auth-baseline.md`](055-user-service-platform-auth-baseline.md).
- Является dependency для frontend protected shell.
- Не должен конфликтовать с уже materialized public auth guard из [`043-openai-chatgpt-public-auth-guard.md`](043-openai-chatgpt-public-auth-guard.md).

## Implementation notes

1. Нужно сохранить явное разделение `admin JWT auth` и `public API key auth`.
2. Нельзя silently расширять guard на public provider routes.
3. Ошибки auth должны быть предсказуемыми и пригодными для frontend login flow.
4. Это quick baseline, а не реализация полного future hardening plan.

## Definition of Done

- `/admin/*` защищены JWT guard.
- `developer` получает доступ к admin routes как `admin`.
- Public OpenAI-compatible provider routes продолжают работать на existing API key semantics.
- Добавлены positive и negative tests для admin JWT path.
- Есть verification notes для happy-path и unauthorized access.

## Initial status

- Current State: planned.
- Next Step: materialize backend auth boundary после стабилизации `user_service` baseline.
- Blockers: none.

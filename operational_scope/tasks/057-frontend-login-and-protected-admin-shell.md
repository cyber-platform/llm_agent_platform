# Frontend login page и protected admin shell для `PoC2`

## Контекст

Текущий frontend уже materialized как local operator UI для monitoring и API key management, но пока не имеет целостного auth flow.

Для Priority 1 зафиксирован быстрый UI baseline:

- login page адаптируется из `services/web_ui_service/frontend`;
- `web_ui_service` используется только как donor code;
- frontend хранит access token без refresh-token flow;
- после login пользователь попадает в protected admin shell;
- logout очищает локальный auth state.

## Goal

Материализовать минимальный, но цельный auth UX во frontend: stylish login screen + protected admin shell поверх backend admin API.

## Scope

В scope:

- адаптация login page из donor-кода `services/web_ui_service/frontend`;
- login form и error states для auth flow;
- локальное хранение access token;
- protected access к admin UI;
- logout flow;
- интеграция с backend admin API после login.

Не входит в scope:

- refresh-token flow;
- полноценный account management UI;
- расширенный RBAC UI;
- перенос `web_ui_service` как runtime dependency;
- multi-provider UI expansion beyond current protected admin shell.

## Canonical references

- [`operational_scope/plans/poc2/poc2-priority-implementation-plan.md`](../plans/poc2/poc2-priority-implementation-plan.md)
- [`docs/architecture/admin-monitoring-read-model.md`](../../docs/architecture/admin-monitoring-read-model.md)
- [`services/frontend/src/App.tsx`](../../services/frontend/src/App.tsx)
- [`services/web_ui_service/frontend/react/src/components/Login.tsx`](../../services/web_ui_service/frontend/react/src/components/Login.tsx)
- [`services/web_ui_service/frontend/react/src/store/appStore.ts`](../../services/web_ui_service/frontend/react/src/store/appStore.ts)

## Dependencies

- Зависит от [`055-user-service-platform-auth-baseline.md`](055-user-service-platform-auth-baseline.md).
- Зависит от [`056-backend-admin-jwt-guard-via-user-service.md`](056-backend-admin-jwt-guard-via-user-service.md).
- Использует current frontend slice из [`045-react-frontend-openai-chatgpt-poc-ui.md`](045-react-frontend-openai-chatgpt-poc-ui.md) как UI baseline.

## Implementation notes

1. Нужно переиспользовать стиль и UX-паттерны, а не переносить старый сервис целиком.
2. Frontend token storage должен оставаться простым и явным, без скрытой auth complexity.
3. После login основным экраном остается current admin/operator shell.
4. Unauthorized state, logout и login errors должны быть явно materialized в UI.

## Definition of Done

- Во frontend есть отдельная login page.
- Login page адаптирована из donor UI и согласована с текущим frontend shell.
- После успешного login пользователь попадает в protected admin shell.
- Без токена admin UI не открывается.
- Logout очищает auth state и возвращает пользователя на login screen.
- Есть verification notes для login, unauthorized state и logout flow.

## Initial status

- Current State: planned.
- Next Step: materialize frontend auth UX после backend admin JWT guard.
- Blockers: none.

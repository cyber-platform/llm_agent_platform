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

## Execution notes

- `services/frontend` получил отдельный login screen, адаптирующий visual patterns donor UI без переноса runtime dependency на `web_ui_service`.
- Frontend хранит access token локально и добавляет Bearer JWT ко всем `/admin/*` запросам.
- Protected shell теперь недоступен без токена; logout и admin unauthorized states возвращают пользователя на login screen с явным session message.

## Materialized changes

- В [`services/frontend/src/LoginPage.tsx`](../../services/frontend/src/LoginPage.tsx) добавлен отдельный stylized login screen с scanner/rain visual motifs и явными error/session banners.
- В [`services/frontend/src/App.tsx`](../../services/frontend/src/App.tsx) materialized local auth session storage, login/logout flow, protected rendering и auto-logout при `missing_bearer_token`/`invalid_token`/`token_expired`/`insufficient_role`.
- В [`services/frontend/src/api.ts`](../../services/frontend/src/api.ts) admin API client переведен на explicit Bearer auth headers, а login flow подключен к `user_service` `POST /auth/login`.
- В [`services/frontend/src/runtime-config.ts`](../../services/frontend/src/runtime-config.ts), [`services/frontend/src/types.ts`](../../services/frontend/src/types.ts) и [`services/frontend/public/runtime-config.json`](../../services/frontend/public/runtime-config.json) добавлен browser runtime setting `authApiBaseUrl`.
- В [`services/frontend/src/styles.css`](../../services/frontend/src/styles.css) добавлены login-specific layout, scanner animations и responsive auth-shell styles; позже scan sweep дополнительно замедлен для менее агрессивного UX.
- В [`services/frontend/README.md`](../../services/frontend/README.md) обновлен service scope и runtime-config section под новый auth contour.
- В [`docker-compose-dev.yml`](../../docker-compose-dev.yml) root dev contour расширен сервисами `user-db` и `user_service`, а также shared JWT env wiring для `backend`, чтобы login flow работал в общей сборке, а не только в isolated `user_service` compose.
- В [`services/user_service/README.md`](../../services/user_service/README.md), [`services/user_service/docs/user_management.md`](../../services/user_service/docs/user_management.md) и [`services/user_service/docs/interaction.md`](../../services/user_service/docs/interaction.md) зафиксирован обязательный prerequisite `uv run alembic upgrade head` перед CLI registration/list/delete scripts и описан failure mode `relation "users" does not exist`.

## Verification trail

- `cd services/frontend && npm run build`
- `docker compose -f docker-compose-dev.yml config`
- `docker exec user-service-dev uv run alembic upgrade head`
- `docker exec user-service-dev uv run python scripts/register_user.py "anton-admin" "12345admin" "developer"`

## Handoff context

- Frontend login flow зависит от доступности `user_service` по `authApiBaseUrl`; для root dev contour это теперь `http://127.0.0.1:8010`, который поднимается тем же `docker-compose-dev.yml`.
- Если `user_service` поднимается на fresh Postgres volume, CLI registration scripts не будут работать до применения Alembic migrations внутри контейнера.
- Для текущего `PoC2` operator login следует создавать пользователя с ролью `developer`, потому что backend admin guard маппит `developer -> admin` только внутри `/admin/*` boundary.
- В рабочем dev contour уже проверен happy path: после `alembic upgrade head` пользователь `anton-admin` был успешно создан через `register_user.py`; этот шаг служит smoke verification для login dependency chain.

## Final status

- Current State: completed.
- Verification: `cd services/frontend && npm run build`; `docker compose -f docker-compose-dev.yml config`; `docker exec user-service-dev uv run alembic upgrade head`; `docker exec user-service-dev uv run python scripts/register_user.py "anton-admin" "12345admin" "developer"`
- Blockers: none.

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

## Execution notes

- `services/backend` получил отдельный admin auth guard для `/admin/*`, не затрагивающий public OpenAI-compatible routes и existing platform API key semantics.
- JWT verification materialized через `JWT_SHARED_SECRET`/`JWT_ISSUER`/`JWT_ALGORITHM`; `developer` маппится в `admin` только внутри backend admin boundary.
- Ошибки guard нормализованы в предсказуемые JSON payloads для missing bearer token, invalid token, expired token и insufficient role.
- Existing admin suites переведены на explicit admin JWT headers, а smoke contour продолжает проверять disjoint admin/public auth paths.

## Materialized changes

- В [`services/backend/llm_agent_platform/api/admin/auth_guard.py`](../../services/backend/llm_agent_platform/api/admin/auth_guard.py) добавлены JWT decode path, claim normalization, `developer -> admin` mapping и error payload helpers.
- В [`services/backend/llm_agent_platform/api/admin/routes.py`](../../services/backend/llm_agent_platform/api/admin/routes.py) подключен `before_request` guard для всего `/admin/*` namespace.
- В [`services/backend/llm_agent_platform/config.py`](../../services/backend/llm_agent_platform/config.py) зафиксированы backend env settings `JWT_SHARED_SECRET`, `JWT_ISSUER`, `JWT_ALGORITHM`.
- В [`services/backend/pyproject.toml`](../../services/backend/pyproject.toml) добавлена dependency `python-jose` для shared-secret JWT verification.
- В [`services/backend/llm_agent_platform/tests/test_admin_auth_guard.py`](../../services/backend/llm_agent_platform/tests/test_admin_auth_guard.py) добавлен suite `TS-ADMIN-JWT-GUARD`, а existing admin suites получили shared auth helpers из [`services/backend/llm_agent_platform/tests/admin_auth_test_utils.py`](../../services/backend/llm_agent_platform/tests/admin_auth_test_utils.py).
- В [`docs/testing/suites/admin-jwt-guard.md`](../../docs/testing/suites/admin-jwt-guard.md), [`docs/testing/test-map.md`](../../docs/testing/test-map.md) и related admin suite pages зафиксирован новый verification contour.

## Verification trail

- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_auth_guard.py llm_agent_platform/tests/test_admin_api_keys.py llm_agent_platform/tests/test_admin_monitoring_read_model.py llm_agent_platform/tests/test_admin_monitoring_refresh.py llm_agent_platform/tests/test_openai_chatgpt_poc_smoke.py llm_agent_platform/tests/test_openai_chatgpt_runtime.py llm_agent_platform/tests/test_refactor_p2_routes.py`

## Handoff context

- Frontend login/protected shell может использовать predictable admin errors `missing_bearer_token`, `invalid_token`, `token_expired`, `insufficient_role` для unauthorized state handling.
- Public `openai-chatgpt` namespace по-прежнему использует только platform API key auth; admin JWT guard не распространяется на `/<provider>/v1/*`.
- Future hardening по observer/admin RBAC, public-key/introspection и audit trail остается вне scope текущего quick baseline.
- Admin guard подключен на уровне `admin_bp.before_request`, поэтому любой новый backend endpoint под `/admin/*` автоматически попадет под JWT verification без дополнительного wiring в route handler.
- Для decode используется shared-secret HS256 baseline из `user_service`; backend ожидает claims `sub`, `user_id`, `role`/`roles`, `iss`, `iat`, `exp`, а issuer по умолчанию синхронизирован как `user_service`.
- Test helper [`services/backend/llm_agent_platform/tests/admin_auth_test_utils.py`](../../services/backend/llm_agent_platform/tests/admin_auth_test_utils.py) уже патчит backend auth settings и выдает валидные admin JWT headers; следующие backend admin tests стоит строить поверх него, чтобы не дублировать signing logic.
- Existing admin suites [`services/backend/llm_agent_platform/tests/test_admin_api_keys.py`](../../services/backend/llm_agent_platform/tests/test_admin_api_keys.py), [`services/backend/llm_agent_platform/tests/test_admin_monitoring_read_model.py`](../../services/backend/llm_agent_platform/tests/test_admin_monitoring_read_model.py), [`services/backend/llm_agent_platform/tests/test_admin_monitoring_refresh.py`](../../services/backend/llm_agent_platform/tests/test_admin_monitoring_refresh.py), [`services/backend/llm_agent_platform/tests/test_openai_chatgpt_poc_smoke.py`](../../services/backend/llm_agent_platform/tests/test_openai_chatgpt_poc_smoke.py) уже адаптированы под новый admin auth contour и служат regression net для disjoint admin/public semantics.
- При установке новой dependency `python-jose` обновился checked-in `services/backend/uv.lock`; дополнительный dependency sync для этой задачи не нужен, если агент не меняет backend dependency graph дальше.
- Верификация public boundary уже включает `test_openai_chatgpt_runtime.py` и `test_refactor_p2_routes.py`; при дальнейших изменениях admin auth важно сохранять их зеленым, потому что они подтверждают отсутствие silent spillover guard-а на public OpenAI-compatible routes.

## Final status

- Current State: completed.
- Verification: `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_admin_auth_guard.py llm_agent_platform/tests/test_admin_api_keys.py llm_agent_platform/tests/test_admin_monitoring_read_model.py llm_agent_platform/tests/test_admin_monitoring_refresh.py llm_agent_platform/tests/test_openai_chatgpt_poc_smoke.py llm_agent_platform/tests/test_openai_chatgpt_runtime.py llm_agent_platform/tests/test_refactor_p2_routes.py`
- Blockers: none.

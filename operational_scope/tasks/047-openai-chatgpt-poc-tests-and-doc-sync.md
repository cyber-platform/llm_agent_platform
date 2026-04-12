# Тесты и doc sync для `openai-chatgpt` PoC

## Контекст

После materialization backend/frontend/delivery pieces PoC нужно собрать verification contour и синхронизировать testing docs.

Эта задача intentionally отделена как integration/doc-sync task, чтобы не смешивать реализацию компонентов и финальную верификацию.

## Goal

Добавить/обновить тесты и testing documentation для всего `openai-chatgpt` PoC: auth guard, admin monitoring, key CRUD и integration smoke path.

## Scope

В scope:

- unit/integration tests для task 042;
- unit/integration tests для task 043;
- unit/integration tests для task 044;
- при наличии frontend test contour — минимальные smoke tests critical flows;
- update `docs/testing/test-map.md`;
- update relevant suite pages в `docs/testing/suites/`;
- финальный verification checklist для demo PoC.

Не входит в scope:

- разработка новых бизнес-решений вне уже зафиксированного PoC scope.

## Canonical references

- [`docs/testing/test-map.md`](../../docs/testing/test-map.md)
- [`docs/testing/suites/admin-monitoring-read-model.md`](../../docs/testing/suites/admin-monitoring-read-model.md)
- [`docs/architecture/admin-monitoring-read-model.md`](../../docs/architecture/admin-monitoring-read-model.md)
- [`docs/architecture/admin-monitoring-refresh-subsystem.md`](../../docs/architecture/admin-monitoring-refresh-subsystem.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)

## Dependencies

- Зависит от задач [`042-openai-chatgpt-api-key-registry-and-admin-crud.md`](042-openai-chatgpt-api-key-registry-and-admin-crud.md), [`043-openai-chatgpt-public-auth-guard.md`](043-openai-chatgpt-public-auth-guard.md), [`044-openai-chatgpt-admin-monitoring-and-activate.md`](044-openai-chatgpt-admin-monitoring-and-activate.md), [`045-react-frontend-openai-chatgpt-poc-ui.md`](045-react-frontend-openai-chatgpt-poc-ui.md) и [`046-local-dev-proxy-and-public-api-exposure.md`](046-local-dev-proxy-and-public-api-exposure.md).

## Verification targets

- invalid / missing / revoked key -> `401 invalid_api_key`;
- valid key -> successful access to public `models` / `chat/completions` path;
- monitoring page payload schema compatibility;
- `Activate` changes preferred account marker;
- key create/list/revoke lifecycle;
- public URL не открывает admin routes.

## Definition of Done

- Тестовый contour покрывает все новые PoC contracts.
- `docs/testing/test-map.md` синхронизирован.
- Новые или обновленные suite pages отражают фактический coverage.
- Есть зафиксированный final smoke checklist для demo.

## Execution Status

- Current State: выполнена.
- Next Step: использовать `TS-OPENAI-CHATGPT-POC-SMOKE` как финальный demo verification contour и поддерживать `docs/testing/` в sync при дальнейших изменениях PoC.
- Blockers: none.

## Completion Notes

- Добавлен финальный smoke suite [`docs/testing/suites/openai-chatgpt-poc-smoke.md`](../../docs/testing/suites/openai-chatgpt-poc-smoke.md) и его реализация [`llm_agent_platform/tests/test_openai_chatgpt_poc_smoke.py`](../../llm_agent_platform/tests/test_openai_chatgpt_poc_smoke.py).
- `docs/testing/test-map.md` синхронизирован с новым PoC verification contour и frontend build smoke.
- Frontend browser-test contour по-прежнему отсутствует; для текущего PoC зафиксирован обязательный `npm run build` smoke вместо UI automation.
- Backend verification выполнен через targeted unittest contour: `test_openai_chatgpt_poc_smoke.py`, `test_admin_api_keys.py`, `test_admin_monitoring_read_model.py`, `test_admin_monitoring_refresh.py`, `test_openai_chatgpt_runtime.py`.
- Frontend verification выполнен через `npm run build` в `services/frontend`; build проходит без ошибок.
- Дополнительно выполнен ручной smoke в Web UI: подтверждены monitoring page, key management flows и operator UX critical paths; сценарии отработали успешно.
- Статус задачи в [`operational_scope/tasks_map.md`](../../operational_scope/tasks_map.md) переведен в `выполнена`, чтобы следующий агент видел закрытый state и актуальный verification context.

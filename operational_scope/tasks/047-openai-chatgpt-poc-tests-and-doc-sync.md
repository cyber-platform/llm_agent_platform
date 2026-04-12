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
- [`docs/architecture/poc-openai-chatgpt-demo.md`](../../docs/architecture/poc-openai-chatgpt-demo.md)

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

- Current State: запланирована.
- Next Step: запускать как финальную integration/doc-sync ветку после реализации основных задач.
- Blockers: зависит от upstream implementation tasks.

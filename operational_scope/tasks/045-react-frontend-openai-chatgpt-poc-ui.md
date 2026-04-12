# React frontend для PoC monitoring и key management

## Контекст

Для demo PoC зафиксирован отдельный локальный React frontend, который работает только как human-facing UI над backend API.

Frontend не публикуется наружу и не читает filesystem artifacts напрямую.

## Goal

Собрать локальный React UI для `openai-chatgpt`, который показывает состояние аккаунтов/квот, позволяет вызывать `Activate` и управлять platform API keys.

## Scope

В scope:

- frontend app structure для PoC;
- dev proxy to backend;
- provider-focused page для `openai-chatgpt`;
- group selector;
- accounts table и quota status;
- `Activate` action;
- API keys list;
- generate key modal с one-shot reveal UX;
- revoke action;
- loading / error / refresh states.

Не входит в scope:

- public deployment frontend;
- auth/RBAC;
- admin API implementation.

## Canonical references

- [`docs/architecture/web-ui.md`](../../docs/architecture/web-ui.md)
- [`docs/architecture/admin-monitoring-read-model.md`](../../docs/architecture/admin-monitoring-read-model.md)
- [`docs/architecture/admin-monitoring-refresh-subsystem.md`](../../docs/architecture/admin-monitoring-refresh-subsystem.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json`](../../docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-keys-list.schema.json`](../../docs/contracts/api/admin/api-keys/openai-chatgpt-api-keys-list.schema.json)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-request.schema.json`](../../docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-request.schema.json)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-response.schema.json`](../../docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-response.schema.json)

## Dependencies

- Зависит от [`042-openai-chatgpt-api-key-registry-and-admin-crud.md`](042-openai-chatgpt-api-key-registry-and-admin-crud.md).
- Зависит от [`044-openai-chatgpt-admin-monitoring-and-activate.md`](044-openai-chatgpt-admin-monitoring-and-activate.md).

## Recommended composition

- `App`
- `AppShell`
- `ProviderPageOpenAIChatGPT`
- `GroupSelector`
- `AccountsPanel`
- `AccountsTable`
- `ApiKeysPanel`
- `GenerateApiKeyModal`
- `GeneratedApiKeyResult`
- `ErrorBanner`

State model:

- page-level selected group;
- monitoring payload + keys list loaded separately;
- mutation -> selective refetch;
- без тяжелого global store.

## Definition of Done

- Frontend поднимается локально и работает через dev proxy на backend.
- UI читает только backend admin API.
- Есть flows: view monitoring, activate account, list keys, generate key, reveal raw key once, revoke key.
- Ошибки и loading states materialized в UI.
- UI не зависит от public internet exposure path.

## Execution Status

- Current State: выполнена.
- Next Step: использовать current frontend slice как baseline для future multi-provider UI decisions, не смешивая его с full target Web UI.
- Blockers: none.

## Completion Notes

- В `services/frontend/` materialized отдельный React frontend для local-only operator UX.
- Provider-focused page для `openai-chatgpt` покрывает monitoring page, group selector, account activation, API key list/create/revoke flows и manual refresh banner/status UX.
- Frontend читает только backend admin API и не зависит от direct filesystem access.
- Same-origin local delivery обеспечивается через dev proxy config в `services/frontend/config/dev-server.json` и runtime config в `services/frontend/public/runtime-config.json`.
- Build smoke зафиксирован в `docs/testing/suites/openai-chatgpt-poc-smoke.md` и проходит через `npm run build` в `services/frontend`.

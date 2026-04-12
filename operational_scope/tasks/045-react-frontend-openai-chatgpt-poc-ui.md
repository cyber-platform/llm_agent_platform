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

- [`docs/architecture/poc-openai-chatgpt-demo.md`](../../docs/architecture/poc-openai-chatgpt-demo.md)
- [`docs/architecture/web-ui.md`](../../docs/architecture/web-ui.md)
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

- Current State: запланирована.
- Next Step: materialize frontend app shell и provider page.
- Blockers: зависит от tasks 042 и 044.

# API key registry и admin CRUD для `openai-chatgpt`

## Контекст

Для demo PoC зафиксирован локальный platform API key registry для `openai-chatgpt`, где один ключ соответствует ровно одному `provider_id` и одной `group_id`.

Storage contract и admin API contracts уже зафиксированы в `docs/contracts/` и `docs/architecture/poc-openai-chatgpt-demo.md`.

Эта задача materialize-ит storage layer и admin CRUD для keys, но не public auth guard.

## Goal

Реализовать локальный registry platform API keys в `secrets/openai-chatgpt/api-keys/registry.json` и admin endpoints для list / create / revoke, совместимые с уже зафиксированными contract schemas.

## Scope

В scope:

- runtime/service layer для чтения и атомарной записи key registry;
- hash-based storage без сохранения raw key;
- `GET /admin/api-keys/openai-chatgpt?group_id=<group_id>`;
- `POST /admin/api-keys/openai-chatgpt`;
- `POST /admin/api-keys/openai-chatgpt/<key_id>/revoke`;
- валидация against provider accounts config groups;
- unit tests для registry и admin CRUD;
- обновление contract/testing docs при необходимости.

Не входит в scope:

- public OpenAI-compatible auth guard;
- frontend UI;
- public internet exposure.

## Canonical references

- [`docs/architecture/poc-openai-chatgpt-demo.md`](../../docs/architecture/poc-openai-chatgpt-demo.md)
- [`docs/contracts/config/openai-chatgpt-api-key-registry.schema.json`](../../docs/contracts/config/openai-chatgpt-api-key-registry.schema.json)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-request.schema.json`](../../docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-request.schema.json)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-response.schema.json`](../../docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-response.schema.json)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-keys-list.schema.json`](../../docs/contracts/api/admin/api-keys/openai-chatgpt-api-keys-list.schema.json)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-revoke-response.schema.json`](../../docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-revoke-response.schema.json)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)

## Dependencies

- Блокеров по архитектуре нет.
- Может выполняться параллельно с [`044-admin-monitoring-read-model-and-activate.md`](044-admin-monitoring-read-model-and-activate.md).
- Public auth guard из [`043-openai-chatgpt-public-auth-guard.md`](043-openai-chatgpt-public-auth-guard.md) зависит от этого registry layer.

## Implementation notes

1. Создать provider-scoped service для key registry.
2. Обеспечить atomic rewrite `registry.json`.
3. При создании ключа:
   - генерировать raw key;
   - сохранять только `key_hash` и metadata;
   - возвращать `raw_api_key` ровно один раз.
4. При revoke не удалять запись, а переводить `status` в `revoked` и проставлять `revoked_at`.
5. Не допускать создание ключа для неизвестной `group_id`.

## Definition of Done

- Registry читается и пишется по contract schema.
- Admin list/create/revoke endpoints возвращают payloads, совместимые с contract schemas.
- Raw key не сохраняется в registry.
- Повторный list не раскрывает raw secret.
- Revoke меняет статус и исключает ключ из future authorization path.
- Добавлены тесты для create/list/revoke и invalid group handling.

## Execution Status

- Current State: запланирована.
- Next Step: реализовать storage/service layer и затем admin endpoints.
- Blockers: none.

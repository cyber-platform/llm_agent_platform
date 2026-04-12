# API key registry и admin CRUD для `openai-chatgpt`

## Контекст

Для demo PoC зафиксирован локальный platform API key registry для `openai-chatgpt`, где один ключ соответствует ровно одному `provider_id` и одной `group_id`.

Storage contract и admin API contracts уже зафиксированы в `docs/contracts/`, [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md) и [`docs/architecture/admin-monitoring-read-model.md`](../../docs/architecture/admin-monitoring-read-model.md).

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

- [`docs/contracts/config/openai-chatgpt-api-key-registry.schema.json`](../../docs/contracts/config/openai-chatgpt-api-key-registry.schema.json)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-request.schema.json`](../../docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-request.schema.json)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-response.schema.json`](../../docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-response.schema.json)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-keys-list.schema.json`](../../docs/contracts/api/admin/api-keys/openai-chatgpt-api-keys-list.schema.json)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-revoke-response.schema.json`](../../docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-revoke-response.schema.json)
- [`docs/architecture/admin-monitoring-read-model.md`](../../docs/architecture/admin-monitoring-read-model.md)
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

- Current State: выполнена в root repo.
- Updated At: `2026-04-12`.
- Completed Work:
  - добавлен provider-scoped registry service в `llm_agent_platform/services/openai_chatgpt_api_keys.py`;
  - registry path вынесен в config как `OPENAI_CHATGPT_API_KEYS_REGISTRY_PATH` с default `secrets/openai-chatgpt/api-keys/registry.json`;
  - реализованы atomic read/write для `registry.json` с начальной auto-bootstrap shape `{"version":1,"provider_id":"openai-chatgpt","keys":[]}`;
  - create flow генерирует `key_id`, `raw_api_key`, `key_hash`, `masked_preview`, `created_at`, возвращает raw secret ровно один раз и не сохраняет raw key в registry;
  - revoke flow не удаляет запись, а переводит `status` в `revoked` и добавляет `revoked_at`;
  - service валидирует `group_id` против `openai-chatgpt` groups из accounts config через существующий provider config loader;
  - добавлен lookup path для active keys (`lookup_active_key`) как dependency для следующей задачи `043-openai-chatgpt-public-auth-guard.md`;
  - добавлены admin routes в `llm_agent_platform/api/admin/routes.py`: `GET /admin/api-keys/openai-chatgpt`, `POST /admin/api-keys/openai-chatgpt`, `POST /admin/api-keys/openai-chatgpt/<key_id>/revoke`;
  - admin blueprint зарегистрирован в `llm_agent_platform/__main__.py`;
  - добавлен test suite `llm_agent_platform/tests/test_admin_api_keys.py` для service persistence, create/list/revoke flow, invalid group handling и revoked-key lookup behavior;
  - обновлены testing docs: `docs/testing/suites/admin-api-keys.md` и `docs/testing/test-map.md`.
- Files Touched:
  - `llm_agent_platform/services/openai_chatgpt_api_keys.py`;
  - `llm_agent_platform/api/admin/routes.py` и `llm_agent_platform/api/admin/__init__.py`;
  - `llm_agent_platform/__main__.py`;
  - `llm_agent_platform/config.py`;
  - `llm_agent_platform/tests/test_admin_api_keys.py`;
  - `docs/testing/suites/admin-api-keys.md`;
  - `docs/testing/test-map.md`;
  - `operational_scope/tasks_map.md`.
- Behavioral Notes:
  - `list_keys(group_id)` возвращает только записи указанной группы и не раскрывает `raw_api_key` или `key_hash`;
  - `create_key(...)` валидирует `group_id`, требует непустой `label`, пишет только hash и metadata, а raw secret отдает только в create response;
  - `revoke_key(key_id)` не удаляет запись из registry, а переводит ее в `revoked` с `revoked_at`;
  - `lookup_active_key(raw_api_key, group_id=...)` является канонической точкой lookup для будущего public auth guard и уже исключает revoked keys;
  - bootstrap registry создается лениво через service shape `version=1`, `provider_id=openai-chatgpt`, `keys=[]`.
- API Surface Materialized:
  - `GET /admin/api-keys/openai-chatgpt?group_id=<group_id>` -> list payload по schema `openai-chatgpt-api-keys-list.schema.json`;
  - `POST /admin/api-keys/openai-chatgpt` -> create payload по schema `openai-chatgpt-api-key-create-response.schema.json`;
  - `POST /admin/api-keys/openai-chatgpt/<key_id>/revoke` -> revoke payload по schema `openai-chatgpt-api-key-revoke-response.schema.json`.
- Verification:
  - `uv run python -m unittest llm_agent_platform/tests/test_admin_api_keys.py`;
  - `uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_runtime.py`;
  - `uv run python -m compileall llm_agent_platform`.
- Verification Coverage:
  - persistence check подтверждает, что registry хранит только `key_hash`, а не raw secret;
  - admin CRUD check подтверждает create/list/revoke flow и group isolation на уровне list response;
  - invalid group check подтверждает `400` для create/list с неизвестным `group_id`;
  - runtime-adjacent check подтверждает, что revoked key больше не проходит через `lookup_active_key(...)`.
- Handoff Notes:
  - следующий агент для задачи `043` должен переиспользовать `OpenAIChatGPTApiKeyRegistryService.lookup_active_key(...)`, а не дублировать hash/registry logic;
  - при реализации public auth guard не нужно читать `registry.json` напрямую из routes/pipeline; единственная точка доступа уже materialized в service layer;
  - `group_id` в public auth flow должен оставаться обязательной частью authorization semantics, потому что один key scoped к одной группе;
  - текущий registry artifact intentionally расположен в `secrets/openai-chatgpt/api-keys/registry.json`, а не в `STATE_DIR`, потому что это admin-managed secret registry, а не quota/runtime state;
  - admin API в этой задаче intentionally остается no-auth local PoC surface;
  - public OpenAI-compatible auth guard в scope этой задачи не входил и еще не materialized.
- Next Step: использовать registry layer в public auth guard из `043-openai-chatgpt-public-auth-guard.md`.
- Blockers: none.

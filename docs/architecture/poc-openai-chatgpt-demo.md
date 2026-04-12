# Freeze fast demo PoC для `openai-chatgpt`

## Назначение

Этот документ фиксирует архитектуру быстрого локального demo PoC, сфокусированного на `openai-chatgpt`.

Его цель — убрать двусмысленность перед handoff задач на реализацию другим агентам.

Степень зрелости: `candidate for freeze`

## Scope PoC

Входит в scope:

- только provider `openai-chatgpt`;
- public OpenAI-compatible API для `models` и `chat/completions`;
- `Web UI` на React как отдельный frontend container/app;
- admin monitoring/read-model surface для локального operator use;
- account activation для provider-local group;
- генерация и revoke platform API keys для групп `openai-chatgpt`;
- внешний internet access только к public OpenAI-compatible endpoint.

Не входит в scope:

- `RBAC`;
- `user service`;
- hardening для shared multi-user deployment;
- public exposure для admin API;
- multi-provider UX;
- provider discovery work;
- expiration, analytics и usage billing для ключей.

## Зафиксированные архитектурные решения

### 1. Provider scope

- Runtime PoC обслуживает только `openai-chatgpt`.
- Текущий provider-centric routing остается каноническим:
  - `GET /openai-chatgpt/v1/models`
  - `GET /openai-chatgpt/<group_id>/v1/models`
  - `POST /openai-chatgpt/v1/chat/completions`
  - `POST /openai-chatgpt/<group_id>/v1/chat/completions`

### 2. Разделение surfaces

В PoC есть два backend surface с разными trust boundaries.

#### Public API surface

- machine-facing;
- OpenAI-compatible;
- единственный backend surface, который можно публиковать во внешний интернет;
- защищен через platform API keys.

#### Admin API surface

- human/operator-facing;
- используется только локальным `Web UI` в границе PoC;
- для текущего PoC работает без auth;
- не должен публиковаться наружу вместе с machine-facing endpoint.

### 3. Frontend boundary

- Frontend — отдельный React app/container.
- Frontend является только presentation и interaction layer.
- Frontend читает данные только через backend HTTP API.
- Frontend не должен читать `secrets/`, `STATE_DIR` и другие filesystem artifacts напрямую.
- Для PoC допустимо, что frontend и backend доставляются локально вместе, но остаются отдельными containers/apps.

### 4. Scope model для API key

- Один platform API key = ровно один `provider_id` + один `group_id`.
- Для текущего PoC `provider_id` всегда равен `openai-chatgpt`.
- Ключ, привязанный к одной группе, не должен авторизовать запросы к другой группе.
- Platform API keys используются только для public OpenAI-compatible API surface.
- Admin actions не используют platform API keys.

### 5. Storage boundary для API keys

- Registry platform API keys живет в `secrets/openai-chatgpt/api-keys/`.
- Начальный storage artifact для PoC: `secrets/openai-chatgpt/api-keys/registry.json`.
- Registry является admin-managed secrets artifact, а не runtime state в `STATE_DIR`.
- Runtime хранит только hash и metadata для выданных ключей.
- Raw secret возвращается только один раз в момент создания.

Рекомендуемая shape registry для PoC:

```json
{
  "version": 1,
  "provider_id": "openai-chatgpt",
  "keys": [
    {
      "key_id": "key_9x2fa1",
      "label": "demo-default-01",
      "group_id": "default",
      "status": "active",
      "key_hash": "sha256:...",
      "masked_preview": "sk-poc-...2fa1",
      "created_at": "2026-04-12T03:20:55Z"
    }
  ]
}
```

### 6. Error contract для invalid key

Невалидный или неавторизованный platform API key должен приводить к OpenAI-style auth error:

- HTTP status: `401`
- `error.type = authentication_error`
- `error.code = invalid_api_key`

Текст message может оставаться implementation-specific, но должен быть семантически эквивалентен `Incorrect API key provided`.

### 7. `Activate` semantics

- `Activate` — это process-global in-memory preferred-account override per `(provider_id, group_id)`.
- `Activate` не изменяет accounts config files.
- `Activate` не создает новый routing mode.
- `Activate` не bypass-ит cooldown, quota block и group isolation safeguards.
- После restart override исчезает; это допустимо в границе PoC.

### 8. UX key management в `Web UI`

Зафиксированное поведение PoC:

- оператор выбирает или открывает группу;
- UI позволяет выполнить `Generate API Key` с human-readable `label`;
- backend возвращает `raw_api_key` ровно один раз в creation response;
- UI явно помечает, что secret показан один раз, и дает copy affordance;
- последующие list/read операции показывают только masked preview и metadata;
- `revoke` поддерживается; editing scope не поддерживается.

### 9. Boundary внешней публикации

- Во внешний интернет может публиковаться только public OpenAI-compatible API.
- Admin API остается local/private в границе PoC.
- Точный механизм exposure (`tunnel`, reverse proxy или эквивалент) является ops decision и не блокирует архитектурный freeze, пока сохраняется описанное выше разделение surfaces.

## Topology PoC

```text
React frontend (локальный operator UI)
  -> admin API surface (только local/private)

Внешний client/tool
  -> public OpenAI-compatible API surface (internet-exposed)
  -> openai-chatgpt runtime pipeline
```

Допустимая physical deployment модель для PoC:

- один backend service/container с двумя HTTP surfaces;
- один frontend service/container;
- externally reachable являются только public API routes.

## Draft admin API

Эти endpoints зафиксированы на уровне route shape для PoC planning:

- `GET /admin/monitoring/providers`
- `GET /admin/monitoring/openai-chatgpt`
- `POST /admin/monitoring/openai-chatgpt/groups/<group_id>/accounts/<account_name>/activate`
- `GET /admin/api-keys/openai-chatgpt?group_id=<group_id>`
- `POST /admin/api-keys/openai-chatgpt`
- `POST /admin/api-keys/openai-chatgpt/<key_id>/revoke`

Freeze на уровне route shape означает, что реализация еще может уточнить payload details, но не должна менять основную HTTP resource model без возврата к этому документу.

Payload contracts для PoC дополнительно фиксируются отдельными schema files в `docs/contracts/`.

## Frontend screen contract

UI PoC требует одну provider-focused page для `openai-chatgpt` со следующими частями:

- group selector или group sections;
- accounts table;
- quota и routing status;
- preferred-account marker;
- action `Activate`;
- секция API keys со сценариями list, generate и revoke.

Frontend может разбивать загрузку данных на несколько backend requests.
Он не должен зависеть от прямого filesystem layout или от timing persisted state.

## Invariants

- provider selection остается URL-scoped, а не model-driven;
- model validation остается provider-local и group-aware;
- auth по public API key проверяется до продолжения provider execution;
- no-auth boundary для admin valid только для local single-user PoC;
- runtime state и secrets остаются разделенными;
- future hardening не должен переиспользовать platform API keys как admin auth.

## Остаточные implementation decisions вне архитектурного freeze

Архитектурные contracts PoC уже зафиксированы. Ниже остаются только implementation-level решения:

- конкретный local frontend/backend dev proxy setup;
- конкретный способ internet exposure на Ubuntu 24.04;
- frontend component tree и UI composition details.

## Что уже готово к implementation handoff

Следующие элементы уже достаточно стабильны для planning реализации:

- backend public auth guard;
- backend admin read-model API;
- backend in-memory activate override;
- backend API key registry и CRUD;
- React frontend для monitoring и key management;
- docs и tests для новой границы PoC.

## Связанные документы

- [`docs/contracts/api/openai/errors/401-invalid-api-key-error.schema.json`](docs/contracts/api/openai/errors/401-invalid-api-key-error.schema.json:1)
- [`docs/contracts/config/openai-chatgpt-api-key-registry.schema.json`](docs/contracts/config/openai-chatgpt-api-key-registry.schema.json:1)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-request.schema.json`](docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-request.schema.json:1)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-response.schema.json`](docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-create-response.schema.json:1)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-keys-list.schema.json`](docs/contracts/api/admin/api-keys/openai-chatgpt-api-keys-list.schema.json:1)
- [`docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-revoke-response.schema.json`](docs/contracts/api/admin/api-keys/openai-chatgpt-api-key-revoke-response.schema.json:1)
- [`docs/contracts/api/admin/monitoring/openai-chatgpt-activate-account-response.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-activate-account-response.schema.json:1)
- [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
- [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)
- [`docs/architecture/web-ui.md`](docs/architecture/web-ui.md:1)
- [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- [`docs/auth.md`](docs/auth.md:1)

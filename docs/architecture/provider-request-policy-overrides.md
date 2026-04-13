# Provider Request Policy Overrides

## Назначение

Этот документ канонизирует provider-scoped request policy overrides для platform API keys.

Он описывает только architecture/runtime semantics для policy-driven request mutation и provider-specific model capabilities overlay.

## Scope

- provider-specific capabilities overlay;
- key-scoped request policy registry;
- pipeline semantics для pass-through и overwrite modes;
- admin boundary для capabilities и request policies.

Не входит в scope:

- provider adapter-specific payload mapping details;
- полный provider model catalog;
- UI implementation details.

## Core decisions

### Pass-through by default

- Базовый runtime режим платформы — pass-through by default.
- Если для `platform API key` отсутствует request policy record, входящий user request не переписывается платформой только на основании provider capability knowledge.
- В этом режиме pipeline выполняет только обычную provider/protocol adaptation.

### Policy-driven mutation only

- Platform-originated request mutation допускается только при наличии active key-scoped request policy.
- Только в этом режиме pipeline вычисляет `effective_request_params` и применяет overwrite/defaulting semantics.

### Capability overlay over provider registry

- Список provider-local моделей принадлежит существующему `provider_registry`.
- Provider capability configuration не является вторым model catalog.
- Capability artifact хранит только provider-specific overlay knowledge: какие platform-supported request params и ограничения подтверждены для конкретной provider-local модели.

### Separate registries

- Capability overlay и request policy registry должны храниться раздельно.
- Capability overlay — provider-owned config artifact.
- Request policy registry — mutable admin/governance artifact.

### Provider remains final runtime authority

- Platform может валидировать policy against own capability registry.
- Эта validation является guardrail, а не абсолютной истиной о provider contract.
- Окончательная runtime truth остаётся за upstream provider.
- Если provider отвергает param/value или их комбинацию, ошибка возвращается честно и не маскируется.

## Artifacts

### Provider catalog baseline

- `provider_registry` остаётся canonical source для provider-local model catalog.
- Для `openai-chatgpt` catalog baseline задаётся в [`services/backend/llm_agent_platform/provider_registry/providers/openai-chatgpt.json`](../../services/backend/llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1).

### Provider capability overlay

- Для `openai-chatgpt` capability overlay хранится в `services/backend/llm_agent_platform/provider_configuration/openai-chatgpt/models.json`.
- Contract schema: [`docs/contracts/config/openai-chatgpt-model-capabilities-registry.schema.json`](../contracts/config/openai-chatgpt-model-capabilities-registry.schema.json:1)
- Example artifact: [`docs/examples/openai-chatgpt-model-capabilities-registry.example.json`](../examples/openai-chatgpt-model-capabilities-registry.example.json:1)

### Request policy registry

- Для `openai-chatgpt` request policy registry хранится в `secrets/openai-chatgpt/policy_registry/registry.json`.
- Contract schema: [`docs/contracts/config/openai-chatgpt-request-policy-registry.schema.json`](../contracts/config/openai-chatgpt-request-policy-registry.schema.json:1)
- Example artifact: [`docs/examples/openai-chatgpt-request-policy-registry.example.json`](../examples/openai-chatgpt-request-policy-registry.example.json:1)

## Pipeline semantics

### Mode 1: no policy record

- auth boundary резолвит `provider_id`, `group_id`, `key_id`;
- pipeline может читать capability knowledge для admin/read-model/optional validation needs;
- request не получает platform-originated model params;
- adapter получает request после обычной provider adaptation only.

### Mode 2: policy record present

- pipeline загружает key policy и capability overlay;
- pipeline вычисляет `effective_request_params`;
- policy `mode=force` принудительно заменяет client value;
- policy `mode=default_if_absent` применяется только когда client value отсутствует;
- adapter маппит normalized params в provider-specific upstream payload.

## Validation semantics

### Platform-level validation

- platform может валидировать model ids / parameter families / values against own capability overlay.
- Эта validation должна быть отключаемой через platform configuration.
- Даже при выключенной capability validation backend обязан проверять structural integrity policy record (`key_id`, `group_id`, JSON shape).

### Provider-level validation

- final contract authority остаётся за provider;
- stale capability overlay или contract drift могут проявиться только на runtime;
- provider-derived error в этом случае не подменяется synthetic platform fallback.

## OpenAI ChatGPT initial scope

Initial materialized scope для `openai-chatgpt`:

- parameter family: `reasoning_effort`
- immediate model families of interest:
  - `gpt-5.4`
  - `gpt-5.4-mini`
  - `gpt-5.3-codex`

Provider capability overlay может later расширяться на другие parameter families, например compatibility constraints и verbosity-related metadata, если это будет подтверждено и канонизировано.

## Admin boundary

Canonical admin API paths для `openai-chatgpt`:

- `GET /admin/model-capabilities/openai-chatgpt/models/<model_id>`
- `GET /admin/request-policies/openai-chatgpt/keys/<key_id>`
- `PUT /admin/request-policies/openai-chatgpt/keys/<key_id>`
- `DELETE /admin/request-policies/openai-chatgpt/keys/<key_id>`

Related schemas:

- [`docs/contracts/api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json`](../contracts/api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json:1)
- [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-read.schema.json`](../contracts/api/admin/request-policies/openai-chatgpt-request-policy-read.schema.json:1)
- [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-request.schema.json`](../contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-request.schema.json:1)
- [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-response.schema.json`](../contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-response.schema.json:1)

## Responsibilities

- `provider_registry` — canonical provider catalog.
- provider capability overlay — platform-supported overrideable/request-related params per provider-local model.
- request policy registry — key-scoped governance intent.
- pipeline — policy resolution and `effective_request_params` computation.
- provider adapter — upstream payload mapping only.

## Related documents

- pipeline canon: [`openai-chat-completions-pipeline.md`](./openai-chat-completions-pipeline.md:1)
- provider page: [`../providers/openai-chatgpt.md`](../providers/openai-chatgpt.md:1)
- traceability: [`traceability-map.md`](./traceability-map.md:1)

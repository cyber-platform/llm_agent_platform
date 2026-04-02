# Provider: `openai-chatgpt`

## Назначение

[`openai-chatgpt`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1) — отдельный provider в provider-centric платформе, который подключается к общему OpenAI-compatible surface через provider-scoped routes.

Общий канон платформы описан в [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1) и [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1). Эта страница фиксирует только provider-specific особенности.

Актуальный provider status также сводится в [`docs/providers/README.md`](docs/providers/README.md:1).

## Public routing

Provider участвует в общем контракте через маршруты:
- `GET /openai-chatgpt/v1/models`
- `POST /openai-chatgpt/v1/chat/completions`
- `GET /openai-chatgpt/<group_name>/v1/models`
- `POST /openai-chatgpt/<group_name>/v1/chat/completions`

Маршруты входят в общий provider-scoped contract из [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1).

## Catalog strategy

Текущий канон для [`openai-chatgpt`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1):
- provider использует static bootstrap catalog;
- live discovery в текущей архитектуре отсутствует;
- список моделей задается через provider descriptor и runtime registry;
- возможное будущее обновление каталога требует отдельного архитектурного решения и не считается частью текущего SoT.

Канонический Source of Truth для полного provider-wide static catalog:
- [`llm_agent_platform/provider_registry/providers/openai-chatgpt.json`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:26)
- точнее секция `catalog.bootstrap.models`

Общий Source of Truth для provider accounts-config semantics:
- [`docs/configuration/provider-accounts-config.md`](docs/configuration/provider-accounts-config.md:1)

Следствие:
- в документации нельзя описывать [`openai-chatgpt`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1) как discovery-capable provider текущего этапа;
- suite и user docs должны ссылаться на static catalog baseline.
- provider accounts-config и group config могут только сужать видимость моделей, но не расширять catalog сверх [`llm_agent_platform/provider_registry/providers/openai-chatgpt.json`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:26).

## Runtime readiness

Текущий статус provider:
- provider namespace и routing уже входят в канон платформы;
- static bootstrap catalog уже входит в канон платформы;
- state contracts для OAuth и usage-limits подготовлены;
- runtime adapter для `chat/completions` реализован поверх private backend surface;
- provider использует общий accounts-config contract платформы и поддерживает `single` и `rounding`;
- monitoring-only usage adapter вынесен в отдельный порт [`llm_agent_platform/services/provider_usage_limits.py`](llm_agent_platform/services/provider_usage_limits.py:1).

Initial static catalog baseline:
- `gpt-5.4`
- `gpt-5.4-mini`
- `gpt-5.3-codex`
- `gpt-5.2-codex`
- `gpt-5.2`
- `gpt-5.1-codex-max`
- `gpt-5.1-codex-mini`

## OAuth state semantics

State contract задается в [`docs/contracts/state/openai-chatgpt-oauth-state.schema.json`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:1).

Канонические правила:
- `provider_id = openai-chatgpt`;
- `access_token` обязателен для runtime use;
- `refresh_token` может присутствовать, если upstream flow его выдает;
- `account_id` трактуется как optional best-effort field;
- при наличии `account_id` runtime может использовать его для provider-specific headers и observability.

Важно:
- отсутствие `account_id` не должно делать OAuth state невалидным на архитектурном уровне;
- `ChatGPT-Account-Id` должен рассматриваться как conditional header, а не как unconditional invariant.
- user OAuth credentials files в `secrets/openai-chatgpt/accounts/*.json` не являются monitoring/state snapshot файлами и не должны использоваться как target для provider usage persistence.

## Runtime backend boundary

[`openai-chatgpt`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1) не следует описывать как простой OpenAI API base URL с Bearer token.

Каноническая трактовка:
- runtime adapter использует отдельный backend contract;
- transport headers могут отличаться от generic OpenAI public API;
- provider-specific transport semantics должны быть инкапсулированы в adapter boundary, а не протекать в общий pipeline.

Текущая runtime boundary:
- bootstrap script: [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py:1)
- auth manager: [`llm_agent_platform/auth/openai_chatgpt_oauth.py`](llm_agent_platform/auth/openai_chatgpt_oauth.py:1)
- provider adapter: [`llm_agent_platform/api/openai/providers/openai_chatgpt.py`](llm_agent_platform/api/openai/providers/openai_chatgpt.py:1)
- streaming adapter обязан нормализовать private Responses stream в strict OpenAI-compatible `chat/completions` SSE contract без дублирования final `tool_calls` arguments и с reasoning через `reasoning_text`.

## Auth failure invariant

Для runtime adapter этого provider канонизируется invariant:
- `one forced refresh retry on auth failure`

Расшифровка:
- при auth failure выполняется один принудительный refresh access token;
- затем выполняется ровно одна повторная попытка runtime request;
- бесконечные auth retry loops недопустимы.

Этот инвариант должен учитываться в runtime design, provider docs и test traceability.

## Usage limits semantics

Usage state contract задается в [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1).

Для текущего канона фиксируется normalized mapping:
- `limits.primary` — primary usage window;
- `limits.secondary` — secondary usage window;
- `used_percent` — основной normalized indicator;
- `reset_at` — optional normalized reset timestamp;
- provider-specific origin сохраняется через `source` и `metadata`.

Следствие:
- общий contract остается provider-agnostic;
- naming `primary` и `secondary` в документации считается каноническим mapping для этого provider;
- raw upstream payload не является Source of Truth.

Общие правила quota/usage для этого provider:
- состояние exhaustion всё равно определяется по runtime error path;
- proactive usage polling, если появится, используется только для observability и monitoring;
- отсутствие proactive usage endpoint не делает provider архитектурно неполным.

Реализованный monitoring adapter:
- [`llm_agent_platform/services/provider_usage_limits.py`](llm_agent_platform/services/provider_usage_limits.py:1) нормализует `primary` и `secondary` окна и пишет snapshot в `STATE_DIR`.

Storage boundary:

- provider-specific usage snapshot относится к monitoring state и должен жить в [`STATE_DIR`](llm_agent_platform/config.py:30);
- snapshot не должен записываться в user credentials files из `secrets/openai-chatgpt/accounts/*.json`;
- path resolution для usage snapshot должна идти через общий platform-level runtime state paths port, а не через provider-local string replacement logic.

## Связанные документы

- Общий auth overview: [`docs/auth.md`](docs/auth.md:1)
- Общий pipeline: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
- Routing ADR: [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1)
- OAuth state contract: [`docs/contracts/state/openai-chatgpt-oauth-state.schema.json`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:1)
- Usage limits contract: [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1)

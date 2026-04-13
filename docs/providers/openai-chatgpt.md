# LLM Provider: `openai-chatgpt`

## Назначение

[`openai-chatgpt`](services/backend/llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1) — `LLM provider` в `LLM provider`-centric платформе, который подключается к общему [`OpenAI-compatible API`](../terms/project/terms/openai-compatible-api.md) через `LLM provider`-scoped routes.

Общий канон платформы описан в [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1) и [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1). Эта страница фиксирует только `LLM provider`-specific особенности.

## Public routing

`LLM provider` участвует в общем контракте через маршруты:

- `GET /openai-chatgpt/v1/models`
- `POST /openai-chatgpt/v1/chat/completions`
- `GET /openai-chatgpt/<group_name>/v1/models`
- `POST /openai-chatgpt/<group_name>/v1/chat/completions`

Маршруты входят в `LLM provider`-scoped contract из [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1).

Для fast demo PoC поверх этих маршрутов фиксируется дополнительный machine-auth boundary:

- public OpenAI-compatible endpoint принимает только platform API key;
- один platform API key привязан ровно к одной provider-local group;
- invalid key должен приводить к OpenAI-style `401` с `type=authentication_error` и `code=invalid_api_key`.

Формальный error contract для этого случая:

- [`docs/contracts/api/openai/errors/401-invalid-api-key-error.schema.json`](docs/contracts/api/openai/errors/401-invalid-api-key-error.schema.json:1)

Для local operator/admin PoC также materialized provider-scoped admin key-management boundary:

- `GET /admin/api-keys/openai-chatgpt?group_id=<group_id>`
- `POST /admin/api-keys/openai-chatgpt`
- `POST /admin/api-keys/openai-chatgpt/<key_id>/revoke`

Эти маршруты остаются local-only admin surface и не являются частью public machine-facing API.

## Catalog strategy

Текущий канон для [`openai-chatgpt`](services/backend/llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1):

- `LLM provider` использует static bootstrap catalog;
- live discovery отсутствует;
- список моделей задается через `abstract provider` descriptor и runtime registry;
- `LLM provider` accounts-config и group config могут только сужать видимость моделей, но не расширять catalog сверх bootstrap baseline.

Source of Truth для catalog baseline:

- [`services/backend/llm_agent_platform/provider_registry/providers/openai-chatgpt.json`](services/backend/llm_agent_platform/provider_registry/providers/openai-chatgpt.json:26)
- [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1)

## Provider capability overlay and request policies

Для `openai-chatgpt` канонизируется отдельный provider capability overlay поверх catalog baseline.

Правила:

- catalog baseline остаётся у `provider_registry`;
- capability overlay не является вторым model catalog;
- capability overlay хранит только platform-supported overrideable/request-related params per provider-local model;
- request mutation не происходит автоматически на основании capability overlay;
- platform-originated overwrite/defaulting допускается только при наличии key-scoped request policy.

Storage boundaries:

- capability overlay: `services/backend/llm_agent_platform/provider_configuration/openai-chatgpt/models.json`
- request policy registry: `secrets/openai-chatgpt/policy_registry/registry.json`

Contracts:

- capability overlay schema: [`docs/contracts/config/openai-chatgpt-model-capabilities-registry.schema.json`](docs/contracts/config/openai-chatgpt-model-capabilities-registry.schema.json:1)
- request policy registry schema: [`docs/contracts/config/openai-chatgpt-request-policy-registry.schema.json`](docs/contracts/config/openai-chatgpt-request-policy-registry.schema.json:1)

Admin boundary:

- `GET /admin/model-capabilities/openai-chatgpt/models/<model_id>`
- `GET /admin/request-policies/openai-chatgpt/keys/<key_id>`
- `PUT /admin/request-policies/openai-chatgpt/keys/<key_id>`
- `DELETE /admin/request-policies/openai-chatgpt/keys/<key_id>`

Initial parameter scope:

- `reasoning_effort`

Initial model families of interest:

- `gpt-5.4`
- `gpt-5.4-mini`
- `gpt-5.3-codex`

Detailed architecture canon for this boundary: [`docs/architecture/provider-request-policy-overrides.md`](docs/architecture/provider-request-policy-overrides.md:1)

## Runtime readiness

Текущий status `LLM provider`:

- `LLM provider` namespace и routing уже входят в канон платформы;
- static bootstrap catalog уже входит в канон платформы;
- `provider implementation` для `chat/completions` реализован поверх private backend surface;
- `LLM provider` использует общий accounts-config contract платформы и поддерживает `single` и `rounding`;
- monitoring subsystem вынесен в `LLM provider`-specific usage adapter [`services/backend/llm_agent_platform/services/provider_usage_limits.py`](services/backend/llm_agent_platform/services/provider_usage_limits.py:1).

Initial static catalog baseline:

- `gpt-5.4`
- `gpt-5.4-mini`
- `gpt-5.3-codex`
- `gpt-5.2-codex`
- `gpt-5.2`
- `gpt-5.1-codex-max`
- `gpt-5.1-codex-mini`

## OAuth state semantics

OAuth state contract задается в [`docs/contracts/state/openai-chatgpt-oauth-state.schema.json`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:1).

Канонические правила:

- `provider_id = openai-chatgpt`;
- `access_token` обязателен для runtime use;
- `refresh_token` может присутствовать, если upstream flow его выдает;
- `account_id` трактуется как optional best-effort field;
- при наличии `account_id` runtime может использовать его для `LLM provider`-specific headers и observability.

Важно:

- отсутствие `account_id` не делает OAuth state невалидным на архитектурном уровне;
- `ChatGPT-Account-Id` трактуется как conditional header, а не как unconditional invariant;
- user OAuth credentials files в `secrets/openai-chatgpt/accounts/*.json` не являются monitoring/state snapshot файлами.

## Runtime backend boundary

[`openai-chatgpt`](services/backend/llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1) нельзя описывать как простой OpenAI API base URL с Bearer token.

Каноническая трактовка:

- `provider implementation` использует отдельный backend contract;
- transport headers могут отличаться от generic OpenAI public API;
- `LLM provider`-specific transport semantics должны быть инкапсулированы внутри `provider implementation` boundary и не протекать в общий pipeline.

Текущая runtime boundary:

- bootstrap script: [`services/backend/scripts/get_openai-chatgpt_credentials.py`](services/backend/scripts/get_openai-chatgpt_credentials.py:1)
- auth manager: [`services/backend/llm_agent_platform/auth/openai_chatgpt_oauth.py`](services/backend/llm_agent_platform/auth/openai_chatgpt_oauth.py:1)
- `provider implementation`: [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:1)

Streaming adapter обязан нормализовать private Responses stream в strict OpenAI-compatible `chat/completions` SSE contract без дублирования final `tool_calls` arguments и с reasoning через `reasoning_text`.

## Auth failure invariant

Для `provider implementation` этого `LLM provider` канонизируется invariant:

- `one forced refresh retry on auth failure`

Расшифровка:

- при auth failure выполняется один принудительный refresh access token;
- затем выполняется ровно одна повторная попытка runtime request;
- бесконечные auth retry loops недопустимы.

## Account-centric monitoring state

Для [`openai-chatgpt`](services/backend/llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1) `LLM provider`-specific monitoring и request observability живут в account-centric layout под [`STATE_DIR`](services/backend/llm_agent_platform/config.py:30):

```text
<STATE_DIR>/openai-chatgpt/
  accounts/
    <account_name>/
      account_state.json
      usage_windows.json
      request_usage.json
  groups/
    <group_id>/
      quota_state.json
```

Канонические контракты:

- [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1)
- [`docs/contracts/state/openai-chatgpt-usage-windows.schema.json`](docs/contracts/state/openai-chatgpt-usage-windows.schema.json:1)
- [`docs/contracts/state/openai-chatgpt-request-usage.schema.json`](docs/contracts/state/openai-chatgpt-request-usage.schema.json:1)
- [`docs/contracts/state/group-quota-state.schema.json`](docs/contracts/state/group-quota-state.schema.json:1)

Legacy `openai-chatgpt-usage-limits` contract больше не является каноном.

### Artifact semantics

- [`account_state.json`](docs/contracts/state/account-state.schema.json:1) — routing/runtime truth;
- `usage_windows.json` — `LLM provider`-specific monitoring truth с short/long windows и refresh metadata;
- `request_usage.json` — request-driven observability state;
- [`quota_state.json`](docs/contracts/state/group-quota-state.schema.json:1) — group-level derived monitoring snapshot.

Persisted files не являются live source для runtime selection или admin UI; сервис работает по in-memory-first модели, а persisted state нужен для startup hydration, restore after restart и audit trail.

## Two-level usage window semantics

Для этого `LLM provider` канонизируется два normalized monitoring windows:

- `short_window` = short-term quota window (`primary` upstream meaning)
- `long_window` = rolling weekly quota window (`secondary` upstream meaning)

Monitoring adapter должен получать эти окна через dedicated usage endpoint, а не через synthetic model requests.

Следствия:

- `usage_windows.json` хранит operator-facing monitoring truth;
- `request_usage.json` не должен перетирать monitoring windows;
- raw upstream payload не является Source of Truth, канонизируется только normalized contract.

## Quota handling semantics

### LLM provider-specific quota handler

Общий strategy layer остаётся `LLM provider`-agnostic, но интерпретация `LLM provider`-specific quota semantics выносится в [`openai-chatgpt`](services/backend/llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1)-specific handler.

Нормализованный результат handler:

- `block_account_until`
- `reason`
- `window_kind`
- `should_refresh_usage_snapshot`

### `429 usage_limit_reached`

`429 usage_limit_reached` нельзя автоматически трактовать как weekly exhausted state.

Если upstream возвращает `resets_at` или `resets_in_seconds`, это трактуется как short-window block с вычислением `block_account_until` и forced refresh monitoring snapshot.

### Long window

Long window трактуется как rolling weekly quota:

- weekly saturation сама по себе не создаёт новый public API error code;
- long window может использоваться как routing hint и admin monitoring signal;
- polling может сократить блокировку при восстановлении rolling window.

Для текущего runtime `openai-chatgpt` фиксируется provider-specific reconciliation rule:

- если monitoring refresh успешно materialize-ил fresh snapshot;
- и `long_window.used_percent < 0.1`;
- и account сейчас помечен роутером как quota exhausted / `quota_blocked`;
- то monitoring subsystem подаёт router-owned signal на clear exhausted state для этого account.

Границы ответственности при этом не меняются:

- `usage_windows.json` остаётся monitoring truth;
- `account_state.json` остаётся router-owned routing truth;
- monitoring не мутирует `account_state.json` напрямую, а вызывает router reconciliation path;
- router очищает и in-memory exhausted state, и persisted `account_state.json`, чтобы block не вернулся после restart/hydrate.

## Public `429` boundary

Внешний OpenAI-compatible `429` contract остаётся минимальным и не расширяется.

Во внешний API допустимы только outcomes из [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1):

- `all_accounts_on_cooldown`
- `all_accounts_exceed_quota`

Internal/admin-only taxonomy может быть богаче и включать, например:

- `blocked_short_window`
- `blocked_long_window`
- `refresh_failed`
- `stale`

Но эти состояния не должны напрямую протекать в public `429` envelope.

## Admin monitoring boundary

Для текущего пилота monitoring UI строится через admin read-model, а не прямым чтением state files.

Контракты:

- `LLM provider` list: [`docs/contracts/api/admin/monitoring/providers-list.schema.json`](docs/contracts/api/admin/monitoring/providers-list.schema.json:1)
- `LLM provider`-specific page for [`openai-chatgpt`](services/backend/llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1): [`docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json:1)

Канонические правила:

- `LLM provider` list появляется динамически по доступным `LLM provider`;
- `LLM provider` page является `LLM provider`-specific read-model boundary;
- table columns, monitoring windows и drawer sections могут отличаться у разных `LLM provider`;
- для текущего этапа единственный `LLM provider` page в UI — [`openai-chatgpt`](services/backend/llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1).

## Monitoring refresh semantics

Для текущего PoC live monitoring refresh строится поверх общей [`admin monitoring refresh subsystem`](docs/architecture/admin-monitoring-refresh-subsystem.md:1).

Platform-wide monitoring runtime abstraction, в которую этот provider встраивается как первый materialized slice, описана в [`docs/architecture/platform-monitoring-runtime.md`](docs/architecture/platform-monitoring-runtime.md:1).

Provider-specific правила для [`openai-chatgpt`](services/backend/llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1):

- refresh обновляет только provider-specific monitoring usage state;
- request-driven observability state остаётся request-driven и не перезапрашивается refresh subsystem;
- background poller refreshes whole provider;
- manual operator refresh тоже refreshes whole provider;
- provider page должна различать `routing truth` и `monitoring freshness`.

Provider-specific refresh contracts:

- [`docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-start-response.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-start-response.schema.json:1)
- [`docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-status.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-refresh-status.schema.json:1)

## `Activate` semantics

`Activate` входит в pilot scope только как session-scoped in-memory preferred-account override.

Это означает:

- action не меняет `LLM provider` config files;
- action не создаёт новый routing mode;
- для `single` меняется preferred account текущего процесса;
- для `rounding` задаётся preferred account внутри уже существующей selection strategy;
- cooldown, exhausted checks, group isolation и rotation safeguards не bypass-ятся.

## Current admin security boundary

Текущий admin surface больше не является no-auth PoC boundary.

Для текущего mini-release baseline зафиксировано:

- admin API защищен JWT guard через `services/user_service` shared-secret contour;
- operator login flow выполняется через `POST /auth/login` в `services/user_service`;
- public `openai-chatgpt` routes по-прежнему используют platform API key auth;
- `developer` маппится в `admin` только внутри backend admin boundary.

Это все еще не final RBAC architecture для shared dev, multi-user или production-like deployment. Дальнейшее hardening должно идти отдельным Stage 2 циклом.

Для demo PoC это означает:

- admin API и operator Web UI уже работают с JWT login boundary;
- internet exposure допускается только для machine-facing OpenAI-compatible surface;
- platform API keys не используются как admin auth substitute.
- local frontend работает через backend/admin proxy path, а checked-in PoC delivery boundary держит frontend и admin surface только на localhost.

Future hardening вынесен в [`operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md`](operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md:1).

## Связанные документы

- Общий auth overview: [`docs/auth.md`](docs/auth.md:1)
- Общий pipeline: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
- Persisted state canon: [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
- Admin monitoring read-model: [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)
- Platform monitoring runtime: [`docs/architecture/platform-monitoring-runtime.md`](docs/architecture/platform-monitoring-runtime.md:1)
- Admin monitoring refresh subsystem: [`docs/architecture/admin-monitoring-refresh-subsystem.md`](docs/architecture/admin-monitoring-refresh-subsystem.md:1)
- Service behavior config: [`docs/configuration/service-behavior-config.md`](docs/configuration/service-behavior-config.md:1)
- Monitoring/admin ADR: [`docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md`](docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md:1)
- Live refresh ADR: [`docs/adr/0022-admin-monitoring-live-refresh-subsystem.md`](docs/adr/0022-admin-monitoring-live-refresh-subsystem.md:1)
- Live refresh ADR: [`docs/adr/0022-admin-monitoring-live-refresh-subsystem.md`](docs/adr/0022-admin-monitoring-live-refresh-subsystem.md:1)

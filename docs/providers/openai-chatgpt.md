# Provider: `openai-chatgpt`

## Назначение

[`openai-chatgpt`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1) — provider в provider-centric платформе, который подключается к общему OpenAI-compatible surface через provider-scoped routes.

Общий канон платформы описан в [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1) и [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1). Эта страница фиксирует только provider-specific особенности.

## Public routing

Provider участвует в общем контракте через маршруты:

- `GET /openai-chatgpt/v1/models`
- `POST /openai-chatgpt/v1/chat/completions`
- `GET /openai-chatgpt/<group_name>/v1/models`
- `POST /openai-chatgpt/<group_name>/v1/chat/completions`

Маршруты входят в provider-scoped contract из [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1).

## Catalog strategy

Текущий канон для [`openai-chatgpt`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1):

- provider использует static bootstrap catalog;
- live discovery отсутствует;
- список моделей задается через provider descriptor и runtime registry;
- provider accounts-config и group config могут только сужать видимость моделей, но не расширять catalog сверх bootstrap baseline.

Source of Truth для catalog baseline:

- [`llm_agent_platform/provider_registry/providers/openai-chatgpt.json`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:26)
- [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1)

## Runtime readiness

Текущий status provider:

- provider namespace и routing уже входят в канон платформы;
- static bootstrap catalog уже входит в канон платформы;
- runtime adapter для `chat/completions` реализован поверх private backend surface;
- provider использует общий accounts-config contract платформы и поддерживает `single` и `rounding`;
- monitoring subsystem вынесен в provider-specific usage adapter [`llm_agent_platform/services/provider_usage_limits.py`](llm_agent_platform/services/provider_usage_limits.py:1).

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
- при наличии `account_id` runtime может использовать его для provider-specific headers и observability.

Важно:

- отсутствие `account_id` не делает OAuth state невалидным на архитектурном уровне;
- `ChatGPT-Account-Id` трактуется как conditional header, а не как unconditional invariant;
- user OAuth credentials files в `secrets/openai-chatgpt/accounts/*.json` не являются monitoring/state snapshot файлами.

## Runtime backend boundary

[`openai-chatgpt`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1) нельзя описывать как простой OpenAI API base URL с Bearer token.

Каноническая трактовка:

- runtime adapter использует отдельный backend contract;
- transport headers могут отличаться от generic OpenAI public API;
- provider-specific transport semantics должны быть инкапсулированы внутри adapter boundary и не протекать в общий pipeline.

Текущая runtime boundary:

- bootstrap script: [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py:1)
- auth manager: [`llm_agent_platform/auth/openai_chatgpt_oauth.py`](llm_agent_platform/auth/openai_chatgpt_oauth.py:1)
- provider adapter: [`llm_agent_platform/api/openai/providers/openai_chatgpt.py`](llm_agent_platform/api/openai/providers/openai_chatgpt.py:1)

Streaming adapter обязан нормализовать private Responses stream в strict OpenAI-compatible `chat/completions` SSE contract без дублирования final `tool_calls` arguments и с reasoning через `reasoning_text`.

## Auth failure invariant

Для runtime adapter этого provider канонизируется invariant:

- `one forced refresh retry on auth failure`

Расшифровка:

- при auth failure выполняется один принудительный refresh access token;
- затем выполняется ровно одна повторная попытка runtime request;
- бесконечные auth retry loops недопустимы.

## Account-centric monitoring state

Для [`openai-chatgpt`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1) provider-specific monitoring и request observability живут в account-centric layout под [`STATE_DIR`](llm_agent_platform/config.py:30):

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
- `usage_windows.json` — provider-specific monitoring truth с short/long windows и refresh metadata;
- `request_usage.json` — request-driven observability state;
- [`quota_state.json`](docs/contracts/state/group-quota-state.schema.json:1) — group-level derived monitoring snapshot.

Persisted files не являются live source для runtime selection или admin UI; сервис работает по in-memory-first модели, а persisted state нужен для restore after restart и audit trail.

## Two-level usage window semantics

Для этого provider канонизируется два normalized monitoring windows:

- `short_window` = short-term quota window (`primary` upstream meaning)
- `long_window` = rolling weekly quota window (`secondary` upstream meaning)

Monitoring adapter должен получать эти окна через dedicated usage endpoint, а не через synthetic model requests.

Следствия:

- `usage_windows.json` хранит operator-facing monitoring truth;
- `request_usage.json` не должен перетирать monitoring windows;
- raw upstream payload не является Source of Truth, канонизируется только normalized contract.

## Quota handling semantics

### Provider-specific quota handler

Общий strategy layer остаётся provider-agnostic, но интерпретация provider-specific quota semantics выносится в [`openai-chatgpt`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1)-specific handler.

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
- polling может сократить блокировку при частичном восстановлении rolling window.

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

- providers list: [`docs/contracts/api/admin/monitoring/providers-list.schema.json`](docs/contracts/api/admin/monitoring/providers-list.schema.json:1)
- provider-specific page for [`openai-chatgpt`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1): [`docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json:1)

Канонические правила:

- provider list появляется динамически по доступным providers;
- provider page является provider-specific read-model boundary;
- table columns, monitoring windows и drawer sections могут отличаться у разных providers;
- для текущего этапа единственный provider page в UI — [`openai-chatgpt`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1).

## `Activate` semantics

`Activate` входит в pilot scope только как session-scoped in-memory preferred-account override.

Это означает:

- action не меняет provider config files;
- action не создаёт новый routing mode;
- для `single` меняется preferred account текущего процесса;
- для `rounding` задаётся preferred account внутри уже существующей selection strategy;
- cooldown, exhausted checks, group isolation и rotation safeguards не bypass-ятся.

## Current admin security boundary

No-auth admin surface допустима только как local single-user PoC boundary.

Это не baseline для shared dev, multi-user или production-like deployment. При первом выходе за этот контекст вопрос auth/RBAC должен вернуться в отдельный Stage 2 цикл.

Future hardening вынесен в [`operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md`](operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md:1).

## Связанные документы

- Общий auth overview: [`docs/auth.md`](docs/auth.md:1)
- Общий pipeline: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
- Persisted state canon: [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
- Admin monitoring read-model: [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)
- Monitoring/admin ADR: [`docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md`](docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md:1)

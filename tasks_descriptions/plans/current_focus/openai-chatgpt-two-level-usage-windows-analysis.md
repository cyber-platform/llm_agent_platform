# OpenAI ChatGPT: two-level usage windows and quota handling

## Scope

Этот документ фиксирует переписанный Stage 2 baseline для two-level quota semantics у [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) после accepted решений `F-001`–`F-004` в [`tasks_descriptions/plans/current_focus`](tasks_descriptions/plans/current_focus:1).

Документ отвечает за:

- canonical state boundary для provider-specific monitoring и request observability;
- ownership and write-path policy на уровне плана;
- internal quota semantics для short and long windows;
- boundary между internal/admin states и public OpenAI-compatible `429` surface.

Документ не определяет auth/RBAC boundary админского UI; это вынесено в [`discussion-f-005-no-auth-admin-surface-boundary-openai-chatgpt-monitoring.md`](tasks_descriptions/plans/current_focus/discussion-f-005-no-auth-admin-surface-boundary-openai-chatgpt-monitoring.md:225).

## Relevant context

### Accepted discussion documents

- [`discussion-f-001-state-and-contract-boundary-openai-chatgpt-monitoring.md`](tasks_descriptions/plans/current_focus/discussion-f-001-state-and-contract-boundary-openai-chatgpt-monitoring.md:178)
- [`discussion-f-002-state-ownership-and-write-paths-openai-chatgpt-monitoring.md`](tasks_descriptions/plans/current_focus/discussion-f-002-state-ownership-and-write-paths-openai-chatgpt-monitoring.md:249)
- [`discussion-f-003-public-429-surface-and-internal-quota-states-openai-chatgpt-monitoring.md`](tasks_descriptions/plans/current_focus/discussion-f-003-public-429-surface-and-internal-quota-states-openai-chatgpt-monitoring.md:288)
- [`discussion-f-004-activate-semantics-and-routing-boundary-openai-chatgpt-monitoring.md`](tasks_descriptions/plans/current_focus/discussion-f-004-activate-semantics-and-routing-boundary-openai-chatgpt-monitoring.md:223)

### Canonical docs and runtime references

- provider page: [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- auth and state narrative: [`docs/auth.md`](docs/auth.md:1)
- usage overview: [`docs/usage.md`](docs/usage.md:1)
- quota/state canon: [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
- quota reset canon: [`docs/architecture/quota-reset-periods-and-account-state.md`](docs/architecture/quota-reset-periods-and-account-state.md:1)
- public `429` schema: [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1)
- account state contract: [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1)
- group quota state contract: [`docs/contracts/state/group-quota-state.schema.json`](docs/contracts/state/group-quota-state.schema.json:1)
- runtime path resolver: [`resolve_runtime_state_paths()`](llm_agent_platform/services/runtime_state_paths.py:48)
- usage adapter: [`OpenAIChatGptUsageLimitsAdapter.fetch_snapshot()`](llm_agent_platform/services/provider_usage_limits.py:37)
- generic `429` classifier: [`classify_429_response()`](llm_agent_platform/services/quota_transport.py:200)
- router event registration: [`quota_account_router.register_event()`](llm_agent_platform/services/account_router.py:369)

## Reference baseline

В reference-проекте [`wham/usage`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:3) usage endpoint возвращает два окна:

- `primary_window`;
- `secondary_window`.

Для нашей платформы принимается canonical interpretation:

- `primary` = short window `5h`;
- `secondary` = long window `7d rolling`.

## Architectural problems solved by this rewrite

Этот baseline устраняет четыре drift-зоны, найденные critic report:

1. legacy `limits.json` и legacy schema больше не считаются каноном;
2. у mutable state artifacts появляется явный owner и единый async persistence law;
3. internal quota taxonomy отделяется от public `429` contract;
4. quota handling и admin monitoring получают общий account-centric boundary.

## Canonical target model

### 1. Service model is in-memory-first

Runtime source of truth живёт только в памяти процесса.

Persisted files нужны только для:

- restore after restart;
- audit trail.

Ни runtime request path, ни admin UI не должны использовать persisted files как live source.

### 2. Canonical account-centric layout

Platform-level canonical layout:

```text
<STATE_DIR>/
  <provider_id>/
    accounts/
      <account_name>/
        account_state.json
        usage_windows.json
        request_usage.json
    groups/
      <group_id>/
        quota_state.json
```

### 3. Artifact semantics

#### [`account_state.json`](docs/contracts/state/account-state.schema.json:1)

Общий router/runtime state account-level:

- `last_used_at`;
- cooldown state;
- `quota_blocked_until`;
- `quota_block_reason`;
- `quota_block_metadata`.

Это единственный канон routing truth на account level.

#### `usage_windows.json`

Provider-specific monitoring truth:

- `short_window`;
- `long_window`;
- `used_percent`;
- `window_minutes`;
- `reset_at`;
- `last_refreshed_at`;
- `next_refresh_at`;
- `refresh_interval_seconds`;
- provider-specific metadata.

#### `request_usage.json`

Provider-specific request observability truth:

- token usage;
- request counters;
- last request summary;
- optional aggregates for observability.

Этот artifact не должен перетирать `usage_windows.json` и не должен участвовать в routing decisions напрямую.

#### [`quota_state.json`](docs/contracts/state/group-quota-state.schema.json:1)

Group-level derived snapshot для monitoring and admin read-model.

Это не routing source of truth.

### 4. Legacy boundary is removed

Legacy `limits.json` и legacy contract [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1) не считаются долгосрочным каноном.

Для downstream rewrite предполагается полная замена этого legacy boundary новыми contract-first artifacts без compatibility bridge.

## Ownership and write-path policy

### Core rules

1. Каждый mutable artifact имеет одного semantic owner.
2. Все mutable state files пишутся только через shared async writer with coalesce semantics.
3. Persistence layer materializes already-prepared payloads и не знает provider business semantics.
4. Backend admin read-model строится из in-memory state, а не из persisted files.

### Ownership matrix

| Artifact | Semantic owner | Persistence path | Read side | Semantics |
| --- | --- | --- | --- | --- |
| [`account_state.json`](docs/contracts/state/account-state.schema.json:1) | router | shared async writer only | router hydrate, admin read-model | routing-critical persisted backup |
| [`quota_state.json`](docs/contracts/state/group-quota-state.schema.json:1) | router snapshot builder | shared async writer only | admin read-model | derived group snapshot |
| `usage_windows.json` | monitoring refresh subsystem | shared async writer only | provider quota handler, admin read-model | latest provider usage snapshot |
| `request_usage.json` | runtime request-usage collector | shared async writer only | admin read-model | request-driven observability state |

### Lifecycle policy

#### Forced refresh

- initiator: provider-specific quota handler or monitoring scheduler;
- allowed effect: refresh only `usage_windows.json` state;
- forbidden effect: mutate [`account_state.json`](docs/contracts/state/account-state.schema.json:1) directly outside router boundary.

#### Startup warmup

- initiator: monitoring subsystem;
- allowed effect: best-effort refresh of `usage_windows.json`;
- forbidden effect: block startup or mutate router state directly.

#### Refresh on unblock

- initiator: monitoring subsystem when unblock threshold is reached;
- allowed effect: refresh `usage_windows.json` and signal router through explicit call boundary;
- forbidden effect: direct write into [`account_state.json`](docs/contracts/state/account-state.schema.json:1) outside router path.

#### Request path updates

- request path may update `request_usage.json`;
- request path must not overwrite `usage_windows.json`;
- request path must not bypass router when changing [`account_state.json`](docs/contracts/state/account-state.schema.json:1).

## Quota interpretation policy

### Core principle

`429 usage_limit_reached` нельзя автоматически считать недельным exhausted состоянием.

Для сервиса важен нормализованный результат:

- можно ли использовать аккаунт сейчас;
- до какого времени он заблокирован;
- по какой причине он заблокирован;
- нужно ли инициировать forced refresh monitoring snapshot.

### Provider-specific quota handler

Для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) вводится provider-specific quota handler, который умеет:

- разбирать `429` payload;
- учитывать `error.type`, `resets_at`, `resets_in_seconds`, `plan_type`;
- при необходимости смотреть latest `usage_windows` snapshot;
- возвращать нормализованный результат:
  - `block_account_until`;
  - `reason`;
  - `window_kind`;
  - `should_refresh_usage_snapshot`.

### Short window

Если есть `usage_limit_reached` и присутствует `resets_at` or `resets_in_seconds`, handler должен:

- вычислить `block_account_until`;
- пометить `window_kind = short_term`;
- инициировать forced refresh usage state.

### Long window

Long window трактуется как rolling weekly quota.

Следствия:

- weekly saturation не считается вечным блоком до фиксированной даты без переоценки;
- polling может сократить блокировку, если rolling window частично восстановился;
- long window используется как routing hint и admin monitoring signal.

## Public `429` boundary

### Public contract stays unchanged

Внешний OpenAI-compatible `429` contract не расширяется.

Во внешний API допустимы только outcomes из [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1):

- `all_accounts_on_cooldown`;
- `all_accounts_exceed_quota`.

### Internal/admin-only taxonomy

Следующие состояния остаются internal or admin-only and must not leak directly into public `429`:

- `blocked_short_window`;
- `blocked_long_window`;
- `refresh_failed`;
- `stale`;
- raw provider label `usage_limit_reached`;
- любые provider-local monitoring states.

### Mapping rule

Public `429` формируется не из raw provider labels, а из агрегированного runtime conclusion:

- если runtime пришёл к `all available accounts are on cooldown` -> `all_accounts_on_cooldown`;
- если runtime пришёл к `all available accounts are exhausted by contract logic` -> `all_accounts_exceed_quota`;
- intermediate provider-specific блокировки остаются internal or admin-only.

## Refresh policy

Periodic refresh — optional provider capability.

Для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) baseline такой:

- regular refresh с configurable interval;
- для пилота recommended default `1 day`;
- forced refresh после `usage_limit_reached`;
- forced refresh при наступлении `block_account_until`;
- startup warmup только best-effort, без блокировки запуска сервиса.

## Relation to admin monitoring UI

Этот план согласован с [`openai-chatgpt-monitoring-frontend-prototype.md`](tasks_descriptions/plans/current_focus/openai-chatgpt-monitoring-frontend-prototype.md:1):

- UI читает только backend admin read-model;
- admin read-model имеет contract-first статус;
- UI row statuses являются internal/admin-only taxonomy;
- persisted files не являются live UI source.

`Activate` не является частью quota semantics и не меняет этот документ на уровне routing law; его semantics отдельно зафиксирована в `F-004` как session-scoped in-memory preferred-account override.

## Implementation sequence

1. Завести contract-first artifacts для `usage_windows.json`, `request_usage.json` и admin read-model в [`docs/contracts/`](docs/contracts:1).
2. Обновить path resolution и state layout вокруг [`resolve_runtime_state_paths()`](llm_agent_platform/services/runtime_state_paths.py:48).
3. Перевести provider monitoring subsystem на canonical `usage_windows.json`.
4. Ввести provider-specific quota handler для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1).
5. Развести request-driven observability в `request_usage.json`.
6. Синхронизировать public `429` mapping tests и provider/runtime docs.

## Agreed decisions

Зафиксировано следующее:

- новым каноном становится account-centric layout с `account_state.json`, `usage_windows.json`, `request_usage.json` и `quota_state.json`;
- legacy `limits.json` не остаётся каноном и не получает постоянный bridge;
- runtime source of truth живёт в памяти, persisted files используются только как restore and audit layer;
- все mutable state files пишутся только через shared async writer;
- `usage_limit_reached` интерпретируется через provider-specific handler и нормализованный `block_account_until`, а не через грубый глобальный `quota_exhausted`;
- public OpenAI-compatible `429` surface не расширяется;
- internal/admin taxonomy может быть богаче public API without contract drift.

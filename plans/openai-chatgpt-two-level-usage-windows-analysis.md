# OpenAI ChatGPT: двухуровневые usage windows и quota handling

## Scope

Этот документ фиксирует согласованную архитектуру для двух окон квот у [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) и синхронизирован с UI-планом в [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:1).

Основания:

- задача [`tasks_descriptions/tasks/039-two-level-openai-chatgpt.md`](tasks_descriptions/tasks/039-two-level-openai-chatgpt.md:1)
- provider канон [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- usage overview [`docs/usage.md`](docs/usage.md:1)
- auth и state контур [`docs/auth.md`](docs/auth.md:1)
- reference parsing в [`externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:1)

## Relevant context для критика

### Канонические документы

- задача-источник: [`tasks_descriptions/tasks/039-two-level-openai-chatgpt.md`](tasks_descriptions/tasks/039-two-level-openai-chatgpt.md:1)
- provider page: [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- auth overview: [`docs/auth.md`](docs/auth.md:1)
- user-facing usage overview: [`docs/usage.md`](docs/usage.md:1)
- usage limits state contract: [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1)
- account state contract: [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1)
- group quota state contract: [`docs/contracts/state/group-quota-state.schema.json`](docs/contracts/state/group-quota-state.schema.json:1)
- общий quota/state канон: [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
- quota reset canon: [`docs/architecture/quota-reset-periods-and-account-state.md`](docs/architecture/quota-reset-periods-and-account-state.md:1)

### Текущая реализация в проекте

- OpenAI usage polling adapter: [`OpenAIChatGptUsageLimitsAdapter.fetch_snapshot()`](llm_agent_platform/services/provider_usage_limits.py:37)
- runtime state path resolver: [`resolve_runtime_state_paths()`](llm_agent_platform/services/runtime_state_paths.py:48)
- state root config: [`STATE_DIR`](llm_agent_platform/config.py:30)
- usage endpoint config: [`OPENAI_CHATGPT_USAGE_URL`](llm_agent_platform/config.py:143)
- OpenAI runtime provider: [`OpenAIChatGPTProvider.execute_non_stream()`](llm_agent_platform/api/openai/providers/openai_chatgpt.py:515)
- OpenAI runtime streaming path: [`OpenAIChatGPTProvider.stream_lines()`](llm_agent_platform/api/openai/providers/openai_chatgpt.py:545)
- generic 429 classifier: [`classify_429_response()`](llm_agent_platform/services/quota_transport.py:200)
- rounding strategy: [`RotateOn429RoundingStrategy.execute_non_stream()`](llm_agent_platform/api/openai/strategies/rotate_on_429_rounding.py:66)
- rounding stream strategy: [`RotateOn429RoundingStrategy.stream()`](llm_agent_platform/api/openai/strategies/rotate_on_429_rounding.py:185)
- router event registration: [`quota_account_router.register_event()`](llm_agent_platform/services/account_router.py:369)

### Текущее фактическое состояние файлов

- account runtime state example: [`../../../../../../data/model_proxy_state/openai-chatgpt/accounts/kristina/account_state.json`](../../../../../../data/model_proxy_state/openai-chatgpt/accounts/kristina/account_state.json:1)
- current usage snapshot example: [`../../../../../../data/model_proxy_state/openai-chatgpt/usage/accounts/kristina/limits.json`](../../../../../../data/model_proxy_state/openai-chatgpt/usage/accounts/kristina/limits.json:1)
- current group snapshot example: [`../../../../../../data/model_proxy_state/openai-chatgpt/groups/g0/quota_state.json`](../../../../../../data/model_proxy_state/openai-chatgpt/groups/g0/quota_state.json:1)

### Reference implementation

- usage endpoint parser: [`parseOpenAiCodexUsagePayload()`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:30)
- usage fetcher: [`fetchOpenAiCodexRateLimitInfo()`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:69)
- reference type contract: [`OpenAiCodexRateLimitInfo`](externel_projects/kilocode/packages/types/src/providers/openai-codex-rate-limits.ts:4)

### Связанный UI-план

- frontend prototype и backend read-model: [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:1)

## Reference baseline

В reference-проекте [`wham/usage`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:3) возвращает два окна:

- `primary_window`
- `secondary_window`

Оба окна нормализуются с полями:

- `usedPercent`
- `windowMinutes`
- `resetsAt`

Это подтверждено типами в [`externel_projects/kilocode/packages/types/src/providers/openai-codex-rate-limits.ts`](externel_projects/kilocode/packages/types/src/providers/openai-codex-rate-limits.ts:4).

Для нашего дизайна принимается canonical interpretation:

- `primary` = short window `5h`
- `secondary` = long window `7d rolling`

## Текущий разрыв

Текущий адаптер [`OpenAIChatGptUsageLimitsAdapter.fetch_snapshot()`](llm_agent_platform/services/provider_usage_limits.py:37) уже умеет читать оба окна из [`OPENAI_CHATGPT_USAGE_URL`](llm_agent_platform/config.py:143).

Но фактический state сейчас неконсистентен:

- account-level router state лежит в [`account_state.json`](../../../../../../data/model_proxy_state/openai-chatgpt/accounts/kristina/account_state.json:1)
- provider-specific usage state лежит отдельно в [`limits.json`](../../../../../../data/model_proxy_state/openai-chatgpt/usage/accounts/kristina/limits.json:1)
- runtime path может перезаписывать usage snapshot payload-ом без окон из [`OpenAIChatGPTProvider.execute_non_stream()`](llm_agent_platform/api/openai/providers/openai_chatgpt.py:515) и [`OpenAIChatGPTProvider.stream_lines()`](llm_agent_platform/api/openai/providers/openai_chatgpt.py:545)
- `429 usage_limit_reached` сейчас слишком легко попадает в generic `quota_exhausted` через [`classify_429_response()`](llm_agent_platform/services/quota_transport.py:200)

## Ключевой вывод

`429 usage_limit_reached` нельзя автоматически считать недельным exhausted состоянием.

Если upstream вернул payload вида:

```text
429: {"error":{"type":"usage_limit_reached","message":"The usage limit has been reached","plan_type":"free","resets_at":1774905291,"resets_in_seconds":16469}}
```

то базовая трактовка должна быть такой:

- аккаунт временно блокируется до `resets_at`
- это short-window block
- это не означает безусловное исчерпание weekly window

Для сервиса важно не имя окна, а нормализованный результат:

- можно ли использовать аккаунт сейчас
- до какого времени он заблокирован
- по какой причине он заблокирован

## Target design

### 1. Общий strategy layer остаётся общим

Общий слой стратегий и маршрутизации продолжает делать только provider-agnostic работу:

- получить upstream response или exception
- выделить базовый класс `rate_limit | quota_exhausted | unknown`
- вызвать provider-specific quota handler
- получить от него нормализованное решение
- передать решение в router state

То есть generic стратегия не должна самостоятельно решать, что означает `usage_limit_reached` для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1).

### 2. Появляется provider-specific quota handler

Для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) нужен отдельный handler, который умеет:

- разбирать `429` payload
- учитывать `error.type`, `resets_at`, `resets_in_seconds`, `plan_type`
- при необходимости смотреть последний `usage_windows` snapshot
- возвращать нормализованный результат:
  - `block_account_until`
  - `reason`
  - `window_kind`
  - `should_refresh_usage_snapshot`

### 3. Источник мониторинга и источник маршрутизации разделяются

#### Monitoring truth

Provider-specific monitoring snapshot должен хранить оба окна как operator-facing truth:

- `short_window`
- `long_window`
- `used_percent`
- `window_minutes`
- `reset_at`
- `refresh metadata`

Для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) этот snapshot наполняется через [`OPENAI_CHATGPT_USAGE_URL`](llm_agent_platform/config.py:143), а не через запрос к модели.

#### Routing truth

Routing state хранит уже нормализованный operational результат:

- `quota_blocked_until`
- `quota_block_reason`
- `quota_block_metadata`

Такой state отвечает на вопрос, может ли аккаунт участвовать в selection сейчас.

### 4. Account-centric state layout фиксируется на уровне платформы

Согласованный layout:

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

#### [`account_state.json`](../../../../../../data/model_proxy_state/openai-chatgpt/accounts/kristina/account_state.json:1)

Общий router/runtime state аккаунта:

- `last_used_at`
- `cooldown`
- `quota_blocked_until`
- `quota_block_reason`
- `quota_block_metadata`

#### `usage_windows.json`

Provider-specific monitoring snapshot по квотам:

- short window
- long window
- `used_percent`
- `window_minutes`
- `reset_at`
- `last_refreshed_at`
- `next_refresh_at`
- `refresh_interval_seconds`
- provider-specific metadata

#### `request_usage.json`

Provider-specific runtime counters и request statistics:

- token usage
- request counters
- last request summary
- optional aggregates для observability

Этот файл не должен перетирать `usage_windows.json`.

#### [`quota_state.json`](../../../../../../data/model_proxy_state/openai-chatgpt/groups/g0/quota_state.json:1)

Group-level агрегированный monitoring snapshot.

## Политика обработки двух окон

### Short window

Если есть `usage_limit_reached` и присутствует `resets_at` или `resets_in_seconds`, handler должен:

- вычислить `block_account_until`
- пометить `window_kind = short_term`
- инициировать forced refresh usage state

### Long window

Long window трактуется как rolling weekly quota.

Следствия:

- weekly exhaustion не должно считаться вечным блоком до фиксированной даты без переоценки
- polling может сократить блокировку, если rolling window частично восстановился
- long window полезен и для routing hints, и для monitoring UI

## Refresh policy

Periodic refresh — это optional provider capability.

Для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) согласованный baseline:

- regular refresh с настраиваемым interval
- для пилота рекомендованный default `1 day`
- forced refresh после `usage_limit_reached`
- forced refresh при наступлении `block_account_until`
- startup warmup только best-effort, без блокировки запуска сервиса

## Итоговые решения

Зафиксировано следующее:

- usage windows для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) всегда отображаются как две отдельные квоты
- общая стратегия остаётся provider-agnostic
- semantics ошибки переводятся в provider-specific quota handler
- сервис опирается на `block_account_until`, а не на грубый бинарный признак `quota_exhausted`
- state layout становится account-centric
- monitoring и runtime request usage разводятся в отдельные provider-specific optional файлы
- refresh capability остаётся provider-specific и configurable

## Следующий этап реализации

После перехода к реализации задача декомпозируется так:

1. Обновить state layout и path resolution вокруг [`resolve_runtime_state_paths()`](llm_agent_platform/services/runtime_state_paths.py:48)
2. Развести `usage_windows.json` и `request_usage.json`
3. Ввести provider-specific quota handler для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1)
4. Перевести `429 usage_limit_reached` на вычисление `block_account_until`
5. Добавить refresh metadata и periodic refresh capability
6. Подготовить read-model для monitoring UI из [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:1)

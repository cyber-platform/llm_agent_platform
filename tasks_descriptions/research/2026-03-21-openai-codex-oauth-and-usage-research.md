# Research: OpenAI Codex OAuth and usage-limits reference for `openai-chatgpt`

Status: draft for discussion

## Scope

Исследование выполнено как вход для runtime-задачи [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1) в рамках research-задачи [`tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md:1).

Цель — понять, какие части upstream reference из [`externel_projects/kilocode/src/integrations/openai-codex/oauth.ts`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:1), [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts:1) и [`externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:1) можно переносить почти буквально в наш runtime, а какие части требуют адаптации под provider-centric границы из [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:21).

## Sources reviewed

- OAuth flow: [`externel_projects/kilocode/src/integrations/openai-codex/oauth.ts`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:1)
- Runtime provider: [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts:1)
- Usage limits flow: [`externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:1)
- Наш foundation contract для OAuth state: [`docs/contracts/state/openai-chatgpt-oauth-state.schema.json`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:1)
- Наш foundation contract для usage limits: [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1)
- Наш provider descriptor: [`llm_agent_platform/provider_registry/providers/openai-chatgpt.json`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1)

## Executive summary

Upstream reference показывает, что интеграция фактически состоит из трех независимых контуров:

1. OAuth Authorization Code + PKCE bootstrap с локальным callback и последующим persisted token state.
2. Runtime chat adapter, который идет не в public OpenAI endpoint, а в приватный backend [`https://chatgpt.com/backend-api/codex`](externel_projects/kilocode/src/api/providers/openai-codex.ts:41).
3. Отдельный usage-limits fetch в [`https://chatgpt.com/backend-api/wham/usage`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:3).

Главный архитектурный вывод: discovery foundation из [`llm_agent_platform/provider_registry/providers/openai-chatgpt.json`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:15) и будущий chat runtime не обязаны использовать один и тот же upstream surface. Discovery может оставаться отдельным provider-scoped lifecycle, а runtime adapter должен иметь собственный backend contract, собственный набор заголовков и свою auth-failure retry semantics.

После дополнительной проверки reference в [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts:985) и общем fetch-layer [`externel_projects/kilocode/src/api/providers/fetchers/modelCache.ts`](externel_projects/kilocode/src/api/providers/fetchers/modelCache.ts:76) фиксируем более строгий вывод: `kilocode` для `openai-codex` не подтверждает live discovery моделей и использует curated static model subset. Для нашего `openai-chatgpt` provider целевым baseline также принимается static catalog without discovery, по аналогии с `gemini-cli` и `qwen-code`; возможный live refresh можно рассматривать только как future extension, а не как обязательную часть текущего runtime scope.

## Findings

### 1. OAuth flow

#### Что делает upstream

- Конфигурация задана в [`OPENAI_CODEX_OAUTH_CONFIG`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:17):
  - authorization endpoint: `https://auth.openai.com/oauth/authorize`
  - token endpoint: `https://auth.openai.com/oauth/token`
  - client id фиксирован в коде
  - redirect URI: `http://localhost:1455/auth/callback`
  - scopes: `openid profile email offline_access`
- Для старта flow используются [`generateCodeVerifier()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:179), [`generateCodeChallenge()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:187), [`generateState()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:195) и [`buildAuthorizationUrl()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:203).
- В URL авторизации добавляются codex-specific параметры `codex_cli_simplified_flow=true` и `originator=kilo-code`, см. [`buildAuthorizationUrl()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:203).
- Token exchange выполняется в [`exchangeCodeForTokens()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:225) через `application/x-www-form-urlencoded`.
- Важный нюанс: `state` валидируется на callback, но не отправляется в token exchange body, потому что upstream его отвергает, см. [`waitForCallback()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:573) и [`exchangeCodeForTokens()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:225).
- Refresh реализован в [`refreshAccessToken()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:280) тем же `application/x-www-form-urlencoded` POST.
- Дедупликация параллельных refresh сделана через поле [`refreshPromise`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:345) в [`OpenAiCodexOAuthManager`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:341).
- Истекание токена проверяется через [`isTokenExpired()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:333) с буфером 5 минут.

#### Что переносимо почти буквально

- Authorization Code + PKCE как bootstrap-механика.
- Локальный callback сервер и state verification.
- Form-urlencoded token exchange и refresh.
- Дедупликация параллельного refresh.
- Предпочтение `id_token` для извлечения account id.

#### Что требует адаптации

- Client id и originator нельзя слепо копировать в наш runtime.
- Storage semantics в upstream завязаны на VS Code secrets через [`loadCredentials()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:423) и [`saveCredentials()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:446); у нас состояние должно жить в `STATE_DIR` и соответствовать [`docs/contracts/state/openai-chatgpt-oauth-state.schema.json`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:1).
- Upstream хранит `expires` как миллисекунды epoch, а наш contract сейчас ожидает `expires_at` как `date-time`, см. [`docs/contracts/state/openai-chatgpt-oauth-state.schema.json`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:39).

### 2. Account id propagation

#### Что делает upstream

- Account id извлекается best-effort из JWT claims через [`extractAccountId()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:100).
- Источники extraction:
  - root `chatgpt_account_id`
  - nested claim `https://api.openai.com/auth.chatgpt_account_id`
  - первый `organizations[].id`
  - см. [`extractAccountIdFromClaims()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:88)
- Значение используется для заголовка `ChatGPT-Account-Id` в runtime provider, см. [`executeRequest()`](externel_projects/kilocode/src/api/providers/openai-codex.ts:341) и [`makeCodexRequest()`](externel_projects/kilocode/src/api/providers/openai-codex.ts:488).
- Заголовок добавляется условно, только если account id удалось получить.

#### Архитектурная оценка

Наш foundation contract сейчас требует обязательный `account_id`, см. [`docs/contracts/state/openai-chatgpt-oauth-state.schema.json`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:7). Это сильнее, чем показывает reference. Upstream не гарантирует получение `accountId`, а трактует его как best-effort enrichment.

Предварительный вывод: для runtime design безопаснее считать `account_id` условным полем state и условным заголовком runtime request, а не unconditional invariant.

### 3. Runtime request path

#### Что делает upstream

- Runtime backend задан константой [`CODEX_API_BASE_URL`](externel_projects/kilocode/src/api/providers/openai-codex.ts:41) = `https://chatgpt.com/backend-api/codex`.
- Запросы идут в `/responses`, см. [`makeCodexRequest()`](externel_projects/kilocode/src/api/providers/openai-codex.ts:488).
- Используется Bearer token, а не API key.
- Обязательные runtime headers:
  - `Authorization: Bearer <token>`
  - `originator`
  - `session_id`
  - `User-Agent`
- Условный header:
  - `ChatGPT-Account-Id`
- Запрос использует `responses`-style payload и stream-oriented processing через [`buildRequestBody()`](externel_projects/kilocode/src/api/providers/openai-codex.ts:208), [`executeRequest()`](externel_projects/kilocode/src/api/providers/openai-codex.ts:341) и [`processEvent()`](externel_projects/kilocode/src/api/providers/openai-codex.ts:842).

#### Что важно для нашего runtime

- Нельзя предполагать, что `openai-chatgpt` runtime — это просто OpenAI-compatible base URL + Bearer token.
- У runtime есть собственный backend surface и собственные transport headers.
- По итогам дополнительной проверки static catalog принимается как baseline, поэтому на текущем этапе не требуется опираться на отдельный live discovery surface.
- Если discovery будет возвращен в scope позже, его нужно будет описывать как отдельный concern внутри provider, а не как следствие codex runtime reference.

### 4. Auth-failure retry semantics

#### Что делает upstream

- При auth failure runtime делает ровно один retry после forced refresh через [`forceRefreshAccessToken()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:379).
- Логика находится в основном request loop, см. [`handleResponsesApiMessage()`](externel_projects/kilocode/src/api/providers/openai-codex.ts:146).
- Если forced refresh не помог, runtime останавливается и возвращает ошибку.

#### Архитектурная оценка

Это хороший кандидат на явный runtime invariant для нашей реализации:

- `one forced refresh retry on auth failure`
- `no unbounded auth retry loop`
- `clear credentials only on likely invalid_grant semantics`

Последний пункт тоже взят из reference: [`OpenAiCodexOAuthTokenError.isLikelyInvalidGrant()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:126).

### 5. Usage limits and reset semantics

#### Что делает upstream

- Usage limits читаются GET-запросом на [`WHAM_USAGE_URL`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:3).
- В ответе ожидаются окна `primary_window` и `secondary_window`, см. [`WhamUsageResponse`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:5).
- Из каждого окна забираются:
  - `used_percent`
  - `limit_window_seconds`
  - `reset_at`
- Нормализация идет через [`parseOpenAiCodexUsagePayload()`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:30).
- `reset_at` upstream трактует как epoch seconds и переводит в milliseconds, см. [`secondsToMs()`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:26).
- Если ни primary, ни secondary окна нет, вызывается ошибка, см. [`fetchOpenAiCodexRateLimitInfo()`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:69).

#### Сопоставление с нашим contract

Наш contract [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1) специально generic и хранит `limits` как map. Это нормально для foundation-stage, но reference показывает более конкретную каноническую форму.

Предварительный mapping:

- `primary_window` -> `limits.primary`
- `secondary_window` -> `limits.secondary`
- `used_percent` -> `limits.<window>.used_percent`
- `limit_window_seconds` -> `limits.<window>.metadata.limit_window_seconds` или производный `window`
- `reset_at` -> `limits.<window>.reset_at` после нормализации в `date-time`
- `plan_type` -> top-level `metadata.plan_type`

## Compatibility matrix

| Область | Совместимость с нашим foundation | Вывод |
|---|---|---|
| OAuth state persistence | высокая | структура state нужна, но storage backend у нас другой |
| PKCE + callback bootstrap | высокая | можно переносить почти буквально |
| `account_id` mandatory semantics | низкая | reference показывает best-effort, не hard requirement |
| Model catalog lifecycle | высокая для static catalog | reference подтверждает curated static subset, а не live discovery |
| Chat runtime transport | низкая | нужен отдельный adapter contract для приватного backend |
| Usage limits state | средняя | generic schema подходит, но нужна каноническая привязка окон |
| Auth retry semantics | высокая | стоит принять как runtime invariant |

## Proposed architecture conclusions

### Conclusion 1. Split discovery и chat runtime

После проверки reference baseline меняется: для текущего scope `openai-chatgpt` следует проектировать как provider со static catalog, аналогично [`gemini-cli`](llm_agent_platform/provider_registry/providers/gemini-cli.json:1) и [`qwen-code`](llm_agent_platform/provider_registry/providers/qwen-code.json:1).

Следствие:

- runtime task [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1) должен проектировать отдельный chat backend contract для приватного Codex-like surface
- model catalog не должен зависеть от live discovery
- возможный refresh catalog может быть только future enhancement после отдельной верификации upstream surface

### Conclusion 2. `account_id` лучше трактовать как conditional field

Если оставить `account_id` обязательным в state, мы закладываем предположение, которого reference не подтверждает. Более безопасная трактовка:

- state может существовать без `account_id`
- runtime добавляет `ChatGPT-Account-Id` только при наличии значения
- для org subscription это documented optimization or requirement, но не universal invariant

### Conclusion 3. Usage limits schema можно не ломать, но нужно закрепить canonical mapping

Foundation schema уже достаточно гибкая. На следующем шаге лучше не менять ее вслепую, а сначала зафиксировать в runtime plan каноническое соответствие `primary` и `secondary` окнам upstream WHAM payload.

### Conclusion 4. Forced refresh retry нужно канонизировать

Это не просто detail реализации, а часть устойчивости runtime. Ее стоит перенести как обязательное правило поведения адаптера.

## Proposed architecture: `UsageLimitsAdapter` as hexagonal port

### Why this port is needed

Reference из [`externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:1) показывает, что способ получения usage-limits tightly coupled к конкретному upstream surface:

- endpoint может быть уникальным для provider
- authentication headers могут быть provider-specific
- shape ответа может быть window-based, quota-bucket-based или вообще plan-based
- semantics `reset_at`, `used_percent`, `limit_window_seconds` и дополнительных полей могут отличаться

Если привязать общий runtime к raw payload конкретного provider, мы потащим provider-specific детали через всю систему. Поэтому целесообразно вынести получение и нормализацию usage state в отдельный port.

### Hexagonal view

#### Port

Предлагаемый inbound contract со стороны application/runtime orchestration:

- `UsageLimitsPort`
- или более явно `ProviderUsageLimitsPort`

Смысл порта:

- orchestration слой знает, что он может запросить normalized usage snapshot для конкретного provider/account context
- orchestration слой не знает upstream endpoint, raw payload shape и правила разбора

В терминах обязанностей порт отвечает на вопрос:

- получить usage-limits состояние provider и вернуть normalized provider-agnostic snapshot для нашего state layer

#### Adapter implementation

Конкретной реализацией порта становится provider-specific adapter. Для текущего research кейса это:

- `OpenAiChatGptUsageLimitsAdapter`

Позже могут появиться:

- `QwenUsageLimitsAdapter`
- `GeminiUsageLimitsAdapter`
- `GoogleVertexUsageLimitsAdapter`

Именно адаптер знает:

- какой URL дергать
- какие headers передавать
- какие credentials использовать
- как интерпретировать reset semantics
- какие provider-specific поля стоит сохранить в metadata

### What is input to the adapter

Минимальный входной контекст для реализации вроде `OpenAiChatGptUsageLimitsAdapter`:

- `provider_id`
- `account_id` optional
- `access_token` или другой auth context
- optional provider metadata из descriptor [`llm_agent_platform/provider_registry/providers/openai-chatgpt.json`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1)
- `fetched_at` optional, если оркестратор хочет сам фиксировать timestamp

Внутри адаптера этот input конвертируется в provider-specific HTTP request.

### What fields should be extracted from provider

#### Generic fields that we should try to produce

Независимо от provider, целевой normalized snapshot должен стремиться извлечь такие сущности:

- `as_of`
- `limits`
- `metadata`
- optional `source`

Для каждого logical limit entry полезны поля:

- `used_percent`
- optional `reset_at`
- optional `window`
- optional `source`
- optional `metadata`

Это уже хорошо согласуется с [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1).

#### Provider-specific raw fields for current OpenAI reference

Из [`WhamUsageResponse`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:5) нужно извлекать:

- `rate_limit.primary_window.used_percent`
- `rate_limit.primary_window.limit_window_seconds`
- `rate_limit.primary_window.reset_at`
- `rate_limit.secondary_window.used_percent`
- `rate_limit.secondary_window.limit_window_seconds`
- `rate_limit.secondary_window.reset_at`
- `plan_type`

### How normalization should work

#### Recommended normalization boundary

Да, нормализация нужна, но только до нашего canonical state envelope, а не до потери provider-specific смысла.

Рекомендованная модель:

1. Adapter fetches raw payload.
2. Adapter extracts meaningful provider-specific fields.
3. Adapter converts them into normalized envelope.
4. Adapter also preserves raw/provider-specific semantics in metadata when they matter.

То есть нормализация должна быть двухслойной:

- слой 1: общий shape, удобный для state persistence и UI/runtime decisions
- слой 2: provider-specific metadata, чтобы не потерять важные детали

#### Proposed normalized shape

Без изменения текущего schema направления это может выглядеть так:

```json
{
  "version": 1,
  "provider_id": "openai-chatgpt",
  "account_id": "optional-account-id",
  "as_of": "2026-03-21T17:00:00Z",
  "limits": {
    "primary": {
      "used_percent": 42,
      "reset_at": "2026-03-21T18:00:00Z",
      "window": "60m",
      "source": "wham.primary_window",
      "metadata": {
        "limit_window_seconds": 3600
      }
    },
    "secondary": {
      "used_percent": 17,
      "reset_at": "2026-03-21T17:30:00Z",
      "window": "30m",
      "source": "wham.secondary_window",
      "metadata": {
        "limit_window_seconds": 1800
      }
    }
  },
  "metadata": {
    "plan_type": "chatgpt-plus",
    "provider_usage_source": "wham"
  }
}
```

В этом варианте:

- orchestration и persistence живут на normalized fields
- provider-specific происхождение данных сохраняется через `source` и `metadata`

#### Semantics of normalized fields

##### Top-level fields

- `as_of`
  - Назначение: момент времени, когда usage snapshot был собран или признан актуальным.
  - Зачем нужен:
    - понимать свежесть данных
    - не путать время сбора данных с `reset_at`
    - сравнивать новый snapshot со старым
  - Важное различие:
    - `as_of` отвечает на вопрос когда мы получили это состояние
    - `reset_at` отвечает на вопрос когда upstream считает, что окно лимита будет сброшено

- `limits`
  - Назначение: канонический контейнер для нормализованных limit entries.
  - Зачем нужен:
    - дать orchestration и state layer единый вход независимо от конкретного provider
    - хранить несколько независимых окон или бакетов лимитов
  - Почему map, а не жесткая схема:
    - у одного provider может быть `primary` и `secondary`
    - у другого может быть `daily` и `monthly`
    - у третьего могут быть `requests`, `tokens`, `images`

- `metadata`
  - Назначение: top-level контейнер для provider-specific данных, которые важны, но не должны ломать общий контракт.
  - Примеры:
    - `plan_type`
    - `provider_usage_source`
    - raw upstream flags
    - дополнительные признаки подписки или billing tier
  - Зачем нужен:
    - сохранить полезный контекст
    - не засорять общий contract узкоспециальными полями

- optional `source`
  - Назначение: показать источник, из которого был получен весь snapshot.
  - Примеры:
    - `wham`
    - `provider-rest-api`
    - `html-scrape`
    - `local-cache`
  - Зачем нужен:
    - observability
    - диагностика качества данных
    - различение live-fetch и fallback scenarios
  - Почему optional:
    - не всем providers это обязательно
    - иногда источник и так очевиден из provider metadata

##### Fields inside each `limits.<entry>`

- `used_percent`
  - Назначение: общий индикатор заполненности конкретного лимитного окна в диапазоне `0..100`.
  - Зачем нужен:
    - это самый portable и простой сигнал для runtime/UI
    - позволяет принимать решения без знания абсолютных квот provider
  - Почему это основной обязательный минимум:
    - далеко не все providers отдают абсолютные значения `used` и `max`
    - percent можно получить и из ratio, и из прямого upstream field

- optional `reset_at`
  - Назначение: момент ожидаемого сброса конкретного лимитного окна.
  - Зачем нужен:
    - строить ETA до снятия лимита
    - понимать, когда имеет смысл retry
    - поддерживать user-facing diagnostics
  - Почему optional:
    - не каждый provider умеет отдавать reset timestamp
    - иногда доступны только coarse windows без точного reset time

- optional `window`
  - Назначение: человекочитаемое или нормализованное обозначение длины окна.
  - Примеры:
    - `60m`
    - `24h`
    - `rolling-3h`
  - Зачем нужен:
    - объяснять природу лимита без разбора provider metadata
    - использовать в UI, логах и документации
  - Почему optional:
    - не у всех providers длина окна известна явно
    - иногда окно выводится только косвенно или вообще не имеет фиксированной длины

- optional `source`
  - Назначение: показать происхождение конкретного limit entry, если внутри одного snapshot лимиты пришли из разных upstream sections.
  - Примеры:
    - `wham.primary_window`
    - `wham.secondary_window`
    - `billing.daily_quota`
  - Зачем нужен:
    - помогает трассировать mapping
    - облегчает debug при изменении upstream payload
  - Почему нужен еще и на entry level:
    - top-level `source` описывает snapshot целиком
    - entry-level `source` позволяет различать происхождение отдельных окон

- optional `metadata`
  - Назначение: сохранить provider-specific детали именно для одного limit entry.
  - Примеры:
    - `limit_window_seconds`
    - raw bucket id
    - confidence flags
    - extra thresholds
  - Зачем нужен:
    - не терять важные детали при нормализации
    - оставить место для эволюции адаптера без немедленного изменения общего schema
  - Почему лучше хранить это здесь:
    - эти данные относятся к конкретному окну лимита, а не ко всему snapshot

#### Reset semantics variants that the adapter must support

Не все providers возвращают явный `reset_at` из API так, как это делает WHAM reference в [`externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:42).

Нужны как минимум два supported сценария:

1. `upstream-reset-at`
   - provider прямо возвращает timestamp сброса
   - adapter только нормализует его в canonical `reset_at`

2. `scheduled-reset-policy`
   - provider не возвращает конкретный timestamp каждого окна
   - вместо этого известна policy сброса, например:
     - requests per day
     - reset каждый день в полночь по `America/Los_Angeles`
   - adapter должен уметь вычислить ближайший `reset_at` из policy и текущего `as_of`

Для таких providers, как Google AI Studio daily quotas, предлагается canonical трактовка:

- `window = daily`
- `reset_at` вычисляется адаптером на основе policy
- provider-specific rule сохраняется в `limits.<entry>.metadata`, например:

```json
{
  "reset_policy": {
    "kind": "fixed_schedule",
    "cadence": "daily",
    "timezone": "America/Los_Angeles",
    "local_time": "00:00"
  }
}
```

Преимущество такого подхода:

- orchestration слой всегда видит готовый `reset_at`
- provider-specific origin расчета не теряется
- один и тот же state contract покрывает и live timestamps, и policy-derived resets

Предварительный вывод: `UsageLimitsAdapter` должен уметь не только парсить upstream `reset_at`, но и вычислять его из provider reset policy, если upstream отдает правило, а не готовый timestamp.

### Do we need provider-specific variant

Да, и его стоит предусмотреть явно.

Но provider-specific variant должен жить не вместо normalized shape, а рядом с ним. Иначе мы потеряем общий runtime contract.

Предлагаемый принцип:

- normalized envelope обязателен для всех providers
- provider-specific details разрешены в `metadata`
- если у provider есть уникальные сущности, которые не укладываются в `limits`, они могут сохраняться в top-level `metadata` или во вложенных `limits.<name>.metadata`

Для `openai-chatgpt` provider-specific вариант уже нужен как минимум для:

- `plan_type`
- raw window source names
- raw `limit_window_seconds`
- возможных future полей WHAM payload, которые не стоит терять при нормализации

### Why this is better than raw passthrough

Преимущества подхода:

- runtime получает единый state contract
- UI и observability слой не обязаны знать shape каждого upstream payload
- при добавлении нового provider меняется только adapter
- provider-specific semantics остаются доступны через metadata

Риски:

- нужно аккуратно описать обязательный минимум normalized fields
- потребуется договориться, какие поля входят в canonical `limits`, а какие остаются provider-specific

### Current recommendation

На текущем этапе выглядит оптимальным зафиксировать такой design:

- порт: `ProviderUsageLimitsPort`
- реализация для текущего scope: `OpenAiChatGptUsageLimitsAdapter`
- обязательный output: normalized snapshot с `as_of`, `limits`, `metadata`
- provider-specific details: сохранять через `source` и `metadata`, а не выносить в общий контракт как жесткие поля

## Additional conclusion: model catalog strategy for `openai-chatgpt`

После проверки `kilocode` фиксируется следующая стратегия:

- `openai-chatgpt` использует static bootstrap catalog
- live discovery не входит в обязательный runtime scope
- поведение должно быть согласовано с static providers вроде [`llm_agent_platform/provider_registry/providers/gemini-cli.json`](llm_agent_platform/provider_registry/providers/gemini-cli.json:1) и [`llm_agent_platform/provider_registry/providers/qwen-code.json`](llm_agent_platform/provider_registry/providers/qwen-code.json:1)
- task boundary и narrative нужно скорректировать так, чтобы не обещать discovery-capable behavior без подтвержденного upstream source

Это позволяет инкапсулировать реализацию каждого provider и не ломать общий state contract под конкретный WHAM-like payload.

## What should be reused literally

- [`generateCodeVerifier()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:179)
- [`generateCodeChallenge()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:187)
- [`generateState()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:195)
- Логика локального callback со state validation из [`waitForCallback()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:573)
- Form-urlencoded token exchange и refresh из [`exchangeCodeForTokens()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:225) и [`refreshAccessToken()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:280)
- Best-effort account extraction logic из [`extractAccountId()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:100)
- One-retry auth recovery semantics из [`handleResponsesApiMessage()`](externel_projects/kilocode/src/api/providers/openai-codex.ts:146)
- Usage payload normalization pattern из [`parseOpenAiCodexUsagePayload()`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:30)

## What should not be copied literally

- VS Code secret storage via [`loadCredentials()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:423) and [`saveCredentials()`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:446)
- Hardcoded client id and originator values from [`OPENAI_CODEX_OAUTH_CONFIG`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:17)
- Assumption that upstream backend URL is part of stable public OpenAI API surface from [`CODEX_API_BASE_URL`](externel_projects/kilocode/src/api/providers/openai-codex.ts:41)
- Raw epoch-millisecond expiration shape, потому что наш state contract уже ориентирован на `date-time`, см. [`docs/contracts/state/openai-chatgpt-oauth-state.schema.json`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:39)

## Recommended next decisions before updating tasks

1. Решить, оставляем ли [`account_id`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:22) обязательным или переводим в optional field.
2. Решить, считаем ли usage windows канонически именованными как `primary` и `secondary` внутри [`limits`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:67).
3. Зафиксировать, что runtime adapter для `openai-chatgpt` использует отдельный backend contract и набор headers, независимый от discovery surface.
4. Зафиксировать forced refresh retry как runtime invariant для задачи [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1).

## Discussion checkpoint

Этот документ намеренно совмещает факты исследования и архитектурный анализ. После согласования выводов отсюда можно:

- обновить [`tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md:1)
- обновить [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)
- при необходимости подготовить follow-up на уточнение contract semantics

До этого момента документ считается черновиком для обсуждения.

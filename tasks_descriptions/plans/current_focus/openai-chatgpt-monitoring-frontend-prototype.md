# Frontend prototype: monitoring UI для provider usage states

## Scope

Этот документ описывает согласованный первый прототип админского monitoring UI и синхронизирован с quota architecture в [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:1).

Пилотный scope:

- без авторизации
- без ролей и разграничений
- только веб-интерфейс администратора сервиса
- первая реализация только для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1)

При этом backend и frontend сразу проектируются в общем модульном виде для поддержки нескольких providers в будущем.

## Relevant context для критика

### Основные документы

- quota architecture: [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:1)
- задача-источник: [`tasks_descriptions/tasks/039-two-level-openai-chatgpt.md`](tasks_descriptions/tasks/039-two-level-openai-chatgpt.md:1)
- provider page: [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- usage overview: [`docs/usage.md`](docs/usage.md:1)
- auth overview: [`docs/auth.md`](docs/auth.md:1)

### Contracts и архитектурные страницы

- usage limits state contract: [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1)
- account state contract: [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1)
- group quota state contract: [`docs/contracts/state/group-quota-state.schema.json`](docs/contracts/state/group-quota-state.schema.json:1)
- общий state layout canon: [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
- quota reset canon: [`docs/architecture/quota-reset-periods-and-account-state.md`](docs/architecture/quota-reset-periods-and-account-state.md:1)
- pipeline and strategy overview: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)

### Текущая реализация и integration points

- state root config: [`STATE_DIR`](llm_agent_platform/config.py:30)
- usage endpoint config: [`OPENAI_CHATGPT_USAGE_URL`](llm_agent_platform/config.py:143)
- runtime state path resolver: [`resolve_runtime_state_paths()`](llm_agent_platform/services/runtime_state_paths.py:48)
- usage polling adapter: [`OpenAIChatGptUsageLimitsAdapter.fetch_snapshot()`](llm_agent_platform/services/provider_usage_limits.py:37)
- OpenAI runtime provider: [`OpenAIChatGPTProvider.execute_non_stream()`](llm_agent_platform/api/openai/providers/openai_chatgpt.py:515)
- OpenAI stream path: [`OpenAIChatGPTProvider.stream_lines()`](llm_agent_platform/api/openai/providers/openai_chatgpt.py:545)
- rounding strategy: [`RotateOn429RoundingStrategy.execute_non_stream()`](llm_agent_platform/api/openai/strategies/rotate_on_429_rounding.py:66)
- rounding stream strategy: [`RotateOn429RoundingStrategy.stream()`](llm_agent_platform/api/openai/strategies/rotate_on_429_rounding.py:185)
- router state updates: [`quota_account_router.register_event()`](llm_agent_platform/services/account_router.py:369)

### Текущее фактическое состояние файлов

- account runtime state example: [`../../../../../../data/model_proxy_state/openai-chatgpt/accounts/kristina/account_state.json`](../../../../../../data/model_proxy_state/openai-chatgpt/accounts/kristina/account_state.json:1)
- current usage snapshot example: [`../../../../../../data/model_proxy_state/openai-chatgpt/usage/accounts/kristina/limits.json`](../../../../../../data/model_proxy_state/openai-chatgpt/usage/accounts/kristina/limits.json:1)
- current group snapshot example: [`../../../../../../data/model_proxy_state/openai-chatgpt/groups/g0/quota_state.json`](../../../../../../data/model_proxy_state/openai-chatgpt/groups/g0/quota_state.json:1)

### Reference implementation

- usage parser: [`parseOpenAiCodexUsagePayload()`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:30)
- usage fetcher: [`fetchOpenAiCodexRateLimitInfo()`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:69)
- reference type contract: [`OpenAiCodexRateLimitInfo`](externel_projects/kilocode/packages/types/src/providers/openai-codex-rate-limits.ts:4)

## Цель UI

UI должен быстро показывать оператору текущее состояние аккаунтов provider и давать минимальные административные действия.

Для пилота UI должен отвечать на вопросы:

- какие аккаунты доступны сейчас
- какие аккаунты заблокированы
- насколько заполнены short и long usage windows
- когда ожидается reset обоих окон
- когда будет следующий refresh monitoring state
- какой аккаунт сейчас активен

## Monitoring source

Для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) мониторинг должен строиться не через запрос к модели, а через dedicated usage endpoint [`OPENAI_CHATGPT_USAGE_URL`](llm_agent_platform/config.py:143).

Это позволяет:

- обновлять usage windows отдельно от runtime request path
- не тратить квоту на synthetic model requests
- использовать `wham/usage` как canonical source для `usage_windows.json`

## Общая архитектура UI

### Layout

Экран делится на две зоны:

- sidebar со списком providers
- основная область выбранного provider

### Sidebar

В пилоте в sidebar будет только [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1), но сам sidebar строится динамически через provider list endpoint.

### Main provider page

Основная страница provider показывает аккаунты **внутри их групп**.

Для пилота это означает:

- provider page верхнего уровня
- group sections внутри provider
- строки аккаунтов внутри каждой группы

## Модульность backend и frontend

### Backend

Backend endpoint проектируется в общем виде для нескольких providers:

- общий provider list contract
- общий provider page contract
- provider-specific capabilities
- provider-specific row fields и drawer sections

### Frontend

Фронтенд также проектируется как модульный набор provider-specific компонентов:

- reusable shell components
- provider-specific columns
- provider-specific drawer sections
- capability-driven actions

Следствие:

- некоторые UI blocks могут существовать только для части providers
- некоторые actions могут быть скрыты для providers без нужной capability
- добавление нового provider не требует пересборки общего shell

## Таблица аккаунтов

### Колонки пилота

Для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) каждая строка аккаунта в пилоте содержит:

- `user name`
- `status`
- `short window quota percent`
- `short window reset at`
- `long window quota percent`
- `long window reset at`
- `refresh datetime`
- `last refreshed at`
- `quota blocked until`
- `block reason`
- action column с кнопкой `Activate`

### Активный аккаунт

Текущий активный аккаунт должен выделяться явно:

- имя пользователя подсвечено зелёным
- optional badge `active`
- кнопка `Activate` disabled

### Состояния строки

Нормализованные состояния строки:

- `healthy`
- `near_short_limit`
- `near_long_limit`
- `blocked_short_window`
- `blocked_long_window`
- `refresh_failed`
- `stale`
- `active`

`active` может быть отдельным флагом и визуально сочетаться с любым quota state.

## Drawer по клику на аккаунт

Для пилота согласован drawer по клику на строку аккаунта.

Назначение drawer:

- не перегружать таблицу техническими деталями
- дать оператору доступ к raw monitoring payload и runtime state

### Что показываем в drawer

#### 1. Raw monitoring payload

Из `usage_windows.json`:

- raw short window
- raw long window
- `used_percent`
- `window_minutes`
- `reset_at`
- provider-specific metadata

#### 2. Refresh metadata

- `last_refreshed_at`
- `next_refresh_at`
- `refresh_interval_seconds`
- `refresh_status`
- `last_refresh_error`

#### 3. Routing state

- `status`
- `quota_blocked_until`
- `block_reason`
- `quota_block_metadata`
- group membership
- summary из `account_state.json`

#### 4. Request usage details

Из `request_usage.json`:

- token usage counters
- last request summary
- optional aggregated request stats

## UI data contract

### Provider list endpoint

`GET /admin/monitoring/providers`

Минимальный payload:

```json
{
  "providers": [
    {
      "provider_id": "openai-chatgpt",
      "label": "OpenAI ChatGPT",
      "account_count": 8,
      "has_monitoring": true
    }
  ]
}
```

### Provider page endpoint

`GET /admin/monitoring/providers/openai-chatgpt/accounts`

Минимальный payload:

```json
{
  "provider_id": "openai-chatgpt",
  "display_name": "OpenAI ChatGPT",
  "capabilities": {
    "supports_activate": true,
    "supports_drawer": true,
    "supports_usage_windows": true
  },
  "refresh_interval_seconds": 86400,
  "groups": [
    {
      "group_id": "g0",
      "display_name": "Default group",
      "accounts": [
        {
          "account_name": "kristina",
          "is_active": true,
          "status": "blocked_short_window",
          "short_window": {
            "used_percent": 72,
            "window_minutes": 300,
            "reset_at": "2026-03-31T03:10:00Z"
          },
          "long_window": {
            "used_percent": 94,
            "window_minutes": 10080,
            "reset_at": "2026-04-02T11:40:00Z"
          },
          "refresh": {
            "last_refreshed_at": "2026-03-30T17:00:00Z",
            "next_refresh_at": "2026-03-31T17:00:00Z",
            "refresh_interval_seconds": 86400,
            "status": "scheduled",
            "last_error": null
          },
          "routing": {
            "quota_blocked_until": "2026-03-31T03:10:00Z",
            "block_reason": "usage_limit_reached",
            "state": "blocked",
            "metadata": {
              "window_kind": "short_term"
            }
          },
          "actions": {
            "can_activate": false,
            "activate_endpoint": "/admin/monitoring/providers/openai-chatgpt/accounts/kristina/activate"
          },
          "drawer": {
            "raw_monitoring_payload": {},
            "raw_request_usage_payload": {},
            "raw_account_state_payload": {}
          }
        }
      ]
    }
  ]
}
```

### Activate endpoint

`POST /admin/monitoring/providers/openai-chatgpt/accounts/<account_name>/activate`

Назначение:

- переключить active account для provider
- вернуть обновлённое provider page state
- позволить UI сразу подсветить нового active account

## Presentation rules

### Цвета progress bars

#### Short window

- `0-69%` — зелёный
- `70-89%` — жёлтый
- `90-100%` — красный

#### Long window

- `0-59%` — зелёный
- `60-84%` — жёлтый
- `85-100%` — красный

Long window подсвечивается раньше, потому что восстанавливается медленнее.

### Default sorting

Рекомендуемый порядок внутри группы:

1. blocked accounts
2. accounts with critical long window
3. accounts with critical short window
4. остальные
5. stale и refresh_failed поднимаются вверх внутри своей зоны риска

## Data sources для backend read-model

Backend provider page агрегирует account-centric state layout из [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:1):

- [`account_state.json`](../../../../../../data/model_proxy_state/openai-chatgpt/accounts/kristina/account_state.json:1)
- `usage_windows.json`
- `request_usage.json`
- [`quota_state.json`](../../../../../../data/model_proxy_state/openai-chatgpt/groups/g0/quota_state.json:1)

Фронтенд не должен читать state files напрямую.

## Что не включать в pilot

Чтобы не раздувать первую версию, в пилот не включаем:

- auth
- RBAC
- editing accounts
- group management UI
- charts и history views
- per-request logs
- manual quota override
- websocket live updates

Пилот = grouped table + drawer + activate action.

## Implementation sequence

### Шаг 1

Сделать backend read-model endpoint для provider list и provider page.

### Шаг 2

Подготовить provider-specific mapping для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1):

- short window
- long window
- refresh metadata
- routing state
- activate capability

### Шаг 3

Сделать frontend shell:

- sidebar providers
- provider page
- grouped account table
- progress bars
- datetime formatting

### Шаг 4

Добавить drawer и activate flow.

## Согласованные решения

Зафиксировано следующее:

- UI pilot только для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1), но архитектура общая для нескольких providers
- accounts отображаются внутри групп
- колонка `status` входит в пилот
- `last refreshed at`, `quota blocked until`, `block reason` входят в пилот
- drawer по клику на аккаунт входит в пилот
- activate action входит в пилот
- активный аккаунт подсвечивается зелёным
- monitoring refresh для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) идёт через dedicated usage endpoint, а не через model request

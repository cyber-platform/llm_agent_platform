# Frontend prototype: monitoring UI for provider usage states

## Scope

Этот документ фиксирует переписанный baseline для первого monitoring UI и синхронизирован с архитектурными freeze-решениями `F-001`–`F-005` в директории [`tasks_descriptions/plans/current_focus`](tasks_descriptions/plans/current_focus:1).

Пилотный scope:

- только для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1);
- только локальный single-user PoC;
- без auth и RBAC только внутри этого локального PoC boundary;
- не shared dev baseline и не production-like deployment;
- UI читает только backend admin API и не читает state files напрямую.

## Architectural alignment

План опирается на уже принятые решения:

- новый account-centric state boundary из [`discussion-f-001-state-and-contract-boundary-openai-chatgpt-monitoring.md`](tasks_descriptions/plans/current_focus/discussion-f-001-state-and-contract-boundary-openai-chatgpt-monitoring.md:178);
- in-memory-first ownership model из [`discussion-f-002-state-ownership-and-write-paths-openai-chatgpt-monitoring.md`](tasks_descriptions/plans/current_focus/discussion-f-002-state-ownership-and-write-paths-openai-chatgpt-monitoring.md:249);
- internal/admin-only taxonomy при неизменном public `429` surface из [`discussion-f-003-public-429-surface-and-internal-quota-states-openai-chatgpt-monitoring.md`](tasks_descriptions/plans/current_focus/discussion-f-003-public-429-surface-and-internal-quota-states-openai-chatgpt-monitoring.md:288);
- `Activate` как session-scoped in-memory preferred-account override из [`discussion-f-004-activate-semantics-and-routing-boundary-openai-chatgpt-monitoring.md`](tasks_descriptions/plans/current_focus/discussion-f-004-activate-semantics-and-routing-boundary-openai-chatgpt-monitoring.md:223);
- no-auth boundary только для local single-user PoC из [`discussion-f-005-no-auth-admin-surface-boundary-openai-chatgpt-monitoring.md`](tasks_descriptions/plans/current_focus/discussion-f-005-no-auth-admin-surface-boundary-openai-chatgpt-monitoring.md:225).

## Goal

UI должен быстро показывать оператору текущее состояние provider accounts и давать минимальный набор операторских действий для живого наблюдения за системой.

Для пилота UI должен отвечать на вопросы:

- какие аккаунты доступны сейчас;
- какие аккаунты временно заблокированы;
- насколько заполнены short и long usage windows;
- когда ожидается reset каждого окна;
- когда был последний refresh monitoring state и когда запланирован следующий;
- какой аккаунт сейчас помечен preferred для текущего процесса.

## Security boundary

### Allowed pilot boundary

No-auth admin surface допустима только если одновременно верны все условия:

- интерфейс используется только локально одним оператором;
- это PoC or exploratory stage;
- нет shared deployment requirement;
- нет требования аудита операторских действий;
- нет требования разделения ролей и прав.

### Return-to-Stage-2 trigger

Вопрос auth and RBAC обязан вернуться в Stage 2, если происходит хотя бы одно из событий:

- UI становится доступен нескольким пользователям;
- UI становится доступен вне локальной машины разработчика;
- UI попадает в shared dev or team-facing environment;
- добавляются mutating actions сильнее, чем текущий in-memory `Activate`;
- появляется требование audit trail для операторских действий;
- появляется требование security review перед rollout.

## Monitoring source and read-model boundary

### Monitoring source

Для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) monitoring строится через dedicated usage endpoint [`OPENAI_CHATGPT_USAGE_URL`](llm_agent_platform/config.py:143), а не через synthetic model requests.

### Read-model boundary

Фронтенд читает только backend admin API.

Backend admin API строит contract-first read-model из:

- in-memory router state;
- in-memory latest monitoring snapshot;
- in-memory latest request-usage snapshot;
- provider capabilities и operator-action availability.

Persisted files не участвуют в live delivery path к UI и нужны только для restore after restart и audit trail согласно [`discussion-f-002-state-ownership-and-write-paths-openai-chatgpt-monitoring.md`](tasks_descriptions/plans/current_focus/discussion-f-002-state-ownership-and-write-paths-openai-chatgpt-monitoring.md:257).

### Multi-provider UI model

Monitoring windows для providers появляются динамически по списку доступных providers из provider list endpoint.

Следствия:

- frontend shell и provider navigation остаются общими;
- provider page является provider-specific экраном;
- набор колонок в account table может отличаться у разных providers;
- drawer является provider-specific и может иметь разные sections и payload shape у разных providers.

На текущем этапе первый и единственный provider в UI — [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1).

## Canonical state inputs

UI и backend read-model опираются на новый канон account-centric artifacts:

- [`account_state.json`](docs/contracts/state/account-state.schema.json:1) как routing/runtime truth;
- `usage_windows.json` как provider-specific monitoring truth;
- `request_usage.json` как provider-specific request observability truth;
- [`quota_state.json`](docs/contracts/state/group-quota-state.schema.json:1) как group-level derived snapshot.

Legacy `limits.json` не считается каноном и не должен использоваться ни UI, ни backend read-model.

## UI data contracts

### Contract status

Admin monitoring API считается contract-first boundary. Payload contracts должны жить в [`docs/contracts/`](docs/contracts:1), а этот план описывает только целевую shape and semantics.

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
      "has_monitoring": true,
      "capabilities": {
        "supports_provider_page": true
      }
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
  "security_boundary": {
    "auth_mode": "none",
    "scope": "local_single_user_poc",
    "shared_deployment_allowed": false
  },
  "refresh_interval_seconds": 86400,
  "groups": [
    {
      "group_id": "default",
      "display_name": "Default group",
      "runtime_group_key": "g0",
      "accounts": [
        {
          "account_name": "kristina",
          "is_preferred_for_session": true,
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
            "activate_endpoint": "/admin/monitoring/providers/openai-chatgpt/accounts/kristina/activate",
            "activate_semantics": "session_scoped_in_memory_preferred_account_override"
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

#### Notes

- `runtime_group_key` допускается только как debug field; operator-facing anchor должен использовать `display_name` и стабильный API-level `group_id`, а не внутренний `g0`;
- row statuses в этом payload являются **admin-only taxonomy** и не меняют public OpenAI-compatible `429` contract.

### Activate endpoint

`POST /admin/monitoring/providers/openai-chatgpt/accounts/<account_name>/activate`

Назначение:

- задать preferred account только для текущего runtime process;
- не менять provider config files;
- не bypass-ить cooldown, exhausted checks, group isolation или rotation safeguards;
- вернуть обновлённое provider page state или action result, достаточный для немедленного UI refresh.

### Provider page contract notes

- provider page payload является contract-first, но provider-specific read-model boundary;
- table columns определяются provider capabilities и provider-specific field set;
- drawer payload и drawer sections определяются provider-specific mapping;
- общий frontend shell не должен предполагать одинаковый набор usage windows, columns или drawer blocks для всех providers.

## Overall UI structure

### Layout

Экран делится на две зоны:

- sidebar со списком providers;
- основная область выбранного provider.

### Sidebar

Список providers строится динамически через provider list endpoint.

В пилоте в sidebar будет только [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1), но архитектура сразу допускает появление новых provider pages без переписывания shell.

### Main provider page

Основная страница provider является provider-specific screen и показывает аккаунты внутри их операторски-нормализованных групп.

Для пилота это означает:

- provider page верхнего уровня;
- group sections внутри provider;
- строки аккаунтов внутри каждой группы.

## Table design

### Pilot columns

Для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) каждая строка аккаунта содержит:

- `user name`;
- `status`;
- `short window quota percent`;
- `short window reset at`;
- `long window quota percent`;
- `long window reset at`;
- `next refresh at`;
- `last refreshed at`;
- `quota blocked until`;
- `block reason`;
- action column с кнопкой `Activate`.

Для других providers колонки могут отличаться. Общий shell должен поддерживать provider-specific column sets.

### Preferred account highlight

Текущий session-preferred account должен выделяться явно:

- имя пользователя подсвечено зелёным;
- optional badge `preferred`;
- кнопка `Activate` disabled для уже выбранного session-preferred account.

### Row states

Нормализованные состояния строки:

- `healthy`;
- `near_short_limit`;
- `near_long_limit`;
- `blocked_short_window`;
- `blocked_long_window`;
- `refresh_failed`;
- `stale`;
- `preferred` как отдельный flag.

Эти состояния являются admin-only vocabulary и не должны трактоваться как public API error codes.

## Drawer

Для пилота согласован drawer по клику на строку аккаунта.

Назначение drawer:

- не перегружать таблицу техническими деталями;
- дать оператору доступ к monitoring payload, request observability и runtime routing state.

Drawer является provider-specific UI block. Для разных providers допустимы разные sections, labels и raw payload fragments.

### Drawer sections

#### Raw monitoring payload

Из `usage_windows.json` shape:

- raw short window;
- raw long window;
- `used_percent`;
- `window_minutes`;
- `reset_at`;
- provider-specific metadata.

#### Refresh metadata

- `last_refreshed_at`;
- `next_refresh_at`;
- `refresh_interval_seconds`;
- `refresh_status`;
- `last_refresh_error`.

#### Routing state

- `status`;
- `quota_blocked_until`;
- `block_reason`;
- `quota_block_metadata`;
- group membership;
- summary из [`account_state.json`](docs/contracts/state/account-state.schema.json:1).

#### Request usage details

Из `request_usage.json` shape:

- token usage counters;
- last request summary;
- optional aggregated request stats.

## Presentation rules

### Color thresholds

#### Shared thresholds for pilot

- `0-60%` — зелёный;
- `61-85%` — жёлтый;
- `86-100%` — красный.

Для пилота short window и long window используют одинаковые пороги. Если для другого provider или следующей итерации понадобятся отдельные thresholds, это будет provider-specific presentation rule.

### Default sorting

Рекомендуемый порядок внутри группы:

1. blocked accounts;
2. accounts with critical long window;
3. accounts with critical short window;
4. остальные;
5. `stale` и `refresh_failed` поднимаются вверх внутри своей зоны риска.

## What is excluded from pilot

Чтобы не раздувать первую версию, в пилот не включаем:

- auth;
- RBAC;
- editing accounts config;
- group management UI;
- charts и history views;
- per-request logs;
- manual quota override;
- websocket live updates;
- shared deployment support.

Пилот = grouped table + drawer + session-scoped `Activate` action внутри local single-user boundary.

## Implementation sequence

### Step 1

Зафиксировать contract-first schema для provider list и provider page admin read-model в [`docs/contracts/`](docs/contracts:1).

### Step 2

Подготовить backend read-model mapping для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1):

- short window;
- long window;
- refresh metadata;
- routing state;
- session-preferred account semantics;
- local PoC security boundary fields.

### Step 3

Сделать frontend shell:

- sidebar providers;
- provider page;
- grouped account table;
- progress bars;
- datetime formatting.

### Step 4

Добавить drawer и `Activate` flow c session-scoped in-memory semantics.

## Agreed decisions

Зафиксировано следующее:

- UI pilot только для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1), но архитектура admin API и frontend shell остаётся общей для нескольких providers;
- provider page и drawer считаются provider-specific blocks, а список providers появляется динамически из доступного provider registry/read-model;
- набор мониторинговых окон, table columns и drawer sections может отличаться у разных providers;
- accounts отображаются внутри групп, но operator-facing group identity не должна сводиться к внутреннему `g0`;
- backend admin API является единственной live boundary для UI;
- row statuses являются admin-only taxonomy;
- `Activate` входит в пилот только как session-scoped in-memory preferred-account override;
- no-auth surface допустима только как local single-user PoC and not as shared-dev baseline;
- monitoring refresh для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) идёт через dedicated usage endpoint, а не через model request.

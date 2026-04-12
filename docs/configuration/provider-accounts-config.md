# Provider accounts-config

## Назначение

[`provider-accounts-config`](docs/contracts/config/provider-accounts-config.schema.json:1) — общий Source of Truth для provider-agnostic параметров аккаунтного контура: `single` или `rounding`, rotation policy, quota reset periods, `quota_scope` и provider-local groups.

Этот документ описывает именно общий конфиг-паттерн, а не provider-specific runtime детали.

## Канонический контракт

- Schema: [`docs/contracts/config/provider-accounts-config.schema.json`](docs/contracts/config/provider-accounts-config.schema.json:1)
- Runtime router: [`services/backend/llm_agent_platform/services/account_router.py`](services/backend/llm_agent_platform/services/account_router.py:114)
- Route/provider resolution: [`services/backend/llm_agent_platform/api/openai/pipeline.py`](services/backend/llm_agent_platform/api/openai/pipeline.py:97)

## Где используется

Provider accounts-config задаётся отдельным файлом на провайдера, например:

- Gemini: [`docs/examples/gemini_accounts_config.example.json`](docs/examples/gemini_accounts_config.example.json:1)
- Qwen: [`docs/examples/qwen_accounts_config.example.json`](docs/examples/qwen_accounts_config.example.json:1)
- OpenAI ChatGPT: [`docs/examples/openai_chatgpt_accounts_config.example.json`](docs/examples/openai_chatgpt_accounts_config.example.json:1)

## Credentials boundary

`accounts.<name>.credentials_path` — это ссылка на пользовательский credentials file в `secrets/`.

Для текущего operator-facing layout используются такие канонические примеры:

- Gemini: `secrets/gemini-cli/accounts/<account_name>.json`
- Qwen: `secrets/qwen_code/accounts/<account_name>.json`
- OpenAI ChatGPT: `secrets/openai-chatgpt/accounts/<account_name>.json`

Для OAuth-based providers важно различать:

- `credentials_path` — путь к user credentials file;
- platform/runtime state — отдельные mutable state файлы в [`STATE_DIR`](services/backend/llm_agent_platform/config.py:30);
- provider-specific monitoring snapshots — тоже отдельные mutable state файлы в [`STATE_DIR`](services/backend/llm_agent_platform/config.py:30).

`credentials_path` не должен использоваться как путь для записи runtime monitoring snapshots или platform state.

## Основные поля

### `mode`

- `single` — используется только `active_account`
- `rounding` — используется rotation pool из `all_accounts` или provider-local group pool

### `rotation_policy`

- `rate_limit_threshold` — после скольких подряд `rate_limit` ошибок аккаунт уходит в cooldown
- `quota_exhausted_threshold` — после скольких подряд quota-exhausted ошибок аккаунт помечается exhausted
- `rate_limit_cooldown_seconds` — длительность cooldown после `rate_limit`
- `random_order` — выбирать следующий аккаунт случайно среди доступных
- `rotate_after_n_successes` — принудительно переключать аккаунт после N успешных запросов

#### Как отключить `rotate_after_n_successes`

Чтобы полностью отключить политику переключения по числу успешных запросов, нужно установить:

- `rotation_policy.rotate_after_n_successes = 0`

Это канонический режим `disabled`:

- schema допускает `0` как минимальное значение [`rotate_after_n_successes`](docs/contracts/config/provider-accounts-config.schema.json:33)
- runtime не выполняет BY-N rotation при `<= 0` в [`QuotaAccountRouter.register_success()`](services/backend/llm_agent_platform/services/account_router.py:232)

### `model_quota_resets`

`model_quota_resets` задаёт период восстановления квоты в формате `DD:HH:MM`.

#### Каноническая семантика

- ключ `default` обязателен
- если для конкретной модели нет отдельного override, runtime использует `default`
- model-specific ключи нужны только для моделей с period, отличным от `default`

Фактическая логика fallback:

- сначала ищется запись по имени модели
- если её нет, используется `default`
- см. [`QuotaAccountRouter._quota_reset_timestamp()`](services/backend/llm_agent_platform/services/account_router.py:582)

Пример:

```json
"model_quota_resets": {
  "default": "07:00:00",
  "gpt-5.4": "14:00:00"
}
```

В таком случае:

- для `gpt-5.4` период будет `14:00:00`
- для всех остальных моделей — `07:00:00`

### `quota_scope`

- `per_model` — exhausted считается отдельно по каждой модели
- `per_provider` — exhausted считается общим на провайдера через sentinel `__provider__`

### `groups`

`groups` — provider-local groups для account pool и model visibility.

Каждая группа содержит:

- `groups.<group_id>.accounts`
- `groups.<group_id>.models`

#### Group model semantics

- если `groups` вообще не заданы, route использует весь provider pool и весь provider catalog
- если `groups` заданы, у каждой группы обязан быть явный `models` list
- режима `group exists, but models omitted => expose all provider models` в текущем contract нет
- group без `models` считается невалидной конфигурацией по [`docs/contracts/config/provider-accounts-config.schema.json`](docs/contracts/config/provider-accounts-config.schema.json:56)

#### Важное ограничение

Group model list может только сужать модели относительно provider-wide catalog, но не расширять его сверх provider descriptor.

## Default group semantics

- `/<provider_name>/v1/*` — default group
- `/<provider_name>/<group_id>/v1/*` — named group
- если `groups` не заданы, default group эквивалентен всему `all_accounts`
- если `groups` заданы, default group определяется runtime как первая группа в конфиге — см. [`_resolve_group_models()`](services/backend/llm_agent_platform/api/openai/pipeline.py:111)

## Связанные документы

- Auth overview: [`docs/auth.md`](docs/auth.md:1)
- Quota rotation architecture: [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)
- Provider page: [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)

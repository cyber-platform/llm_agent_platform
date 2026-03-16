# 🔐 Руководство по авторизации

Прокси поддерживает два независимых контура авторизации:
- Gemini OAuth quota (Google Cloud Code / `gemini-cli` совместимый поток).
- Qwen OAuth quota (device flow).

Также опционально поддерживается Vertex AI через сервисный аккаунт.

---

## 1) Gemini OAuth quota

### Что создаётся
- Базовый файл OAuth: `secrets/gemini_cli/user_credentials.json`.
- Далее пользователь может вручную переименовывать/копировать его в именованные аккаунты (например, `secrets/gemini_cli/accounts/lisa.json`, `secrets/gemini_cli/accounts/petr.json`) и указывать их в `secrets/gemini_cli/accounts_config.json`.

### Шаги
1. Установите зависимости:
   ```bash
   uv sync
   ```
2. Запустите OAuth-скрипт:
   ```bash
   uv run python scripts/get_oauth_credentials.py
   ```
3. Пройдите авторизацию в браузере.

Скрипт использует loopback callback (`127.0.0.1`) и динамический порт, с ручным fallback при timeout.

Полезные переменные окружения:
- `NO_BROWSER=true` — не открывать браузер автоматически.
- `OAUTH_CALLBACK_PORT=NNNN` — фиксированный порт callback-сервера.
- `OAUTH_CALLBACK_HOST=127.0.0.1` — bind-адрес callback-сервера.
- `USER_GEMINI_CREDS_PATH=secrets/gemini_cli/user_credentials.json` — путь сохранения credentials.

---

## 2) Qwen OAuth quota

### Что создаётся
- Базовый файл OAuth: `secrets/qwen_code/user_credentials.json`.
- Далее пользователь может вручную переименовывать/копировать его в именованные аккаунты (например, `secrets/qwen_code/accounts/lisa.json`, `secrets/qwen_code/accounts/petr.json`) и указывать их в `secrets/qwen_code/accounts_config.json`.
- В credentials также сохраняется `client_id` (runtime refresh прокси использует именно его).

### Шаги
1. Запустите OAuth device-flow скрипт:
   ```bash
   uv run python scripts/get_qwen_oauth_credentials.py
   ```
2. Откройте ссылку в браузере и завершите подтверждение.
3. Скрипт дождётся токена и сохранит credentials в `secrets/qwen_code/user_credentials.json`.

Рекомендованный `QWEN_OAUTH_SCOPE` по parity с upstream `qwen-code`:
- `openid profile email model.completion`
- источник: `qwen-code/packages/core/src/qwen/qwenOAuth2.ts` (`QWEN_OAUTH_SCOPE`)

Важно по разделению bootstrap/runtime:
- `QWEN_OAUTH_CLIENT_ID` и `QWEN_OAUTH_SCOPE` нужны для bootstrap device-flow (скрипт `scripts/get_qwen_oauth_credentials.py`).
- Runtime прокси при refresh берёт `client_id` из credentials-файла аккаунта.

---

## 3) Конфиги ротации аккаунтов (single/rounding)

Источник политики ротации — только provider-конфиги:
- `secrets/gemini_cli/accounts_config.json`
- `secrets/qwen_code/accounts_config.json`

Примеры структуры вынесены в отдельные файлы:
- Gemini: [`docs/examples/gemini_accounts_config.example.json`](docs/examples/gemini_accounts_config.example.json:1)
- Qwen: [`docs/examples/qwen_accounts_config.example.json`](docs/examples/qwen_accounts_config.example.json:1)

Для Qwen в `accounts.<name>` достаточно `credentials_path`; поле `project_id` не требуется.

Режимы:
- `single` — используется только `active_account`.
- `rounding` — round-robin по `all_accounts` с раздельной обработкой `rate_limit` (cooldown) и `quota_exhausted` (exhausted-until).

Опции `rotation_policy` (актуально для `rounding`):
- `rotation_policy.random_order`: при переключении выбирать следующий аккаунт случайно из доступных.
- `rotation_policy.rotate_after_n_successes`: принудительно переключать аккаунт после N успешных запросов.

Quota groups (URL-prefix вариант B):
- В provider-config можно задать `groups`: `groups.<group_id>.accounts` и `groups.<group_id>.models`.
- Для вызовов OpenAI-compatible API можно использовать префикс `/<group_id>/v1/*` (например, `/<group_id>/v1/chat/completions`).
- Без префикса используется дефолтная группа `g0`.
- Важно: если `groups` присутствует, то `GET /v1/models` и `GET /<group_id>/v1/models` берут модели из `groups.<group_id>.models` (по всем провайдерам). Поэтому в `groups.g0.models` нужно явно задать модели для дефолтного пути `/v1/models`.

### Breaking: `model_quota_resets` как период восстановления квоты
`model_quota_resets` теперь задаёт **период восстановления квоты**, формат `DD:HH:MM`.

Семантика exhausted:
- при фиксации quota-exhausted запоминаем момент `quota_exhausted_at`;
- до истечения `quota_exhausted_at + model_quota_resets[model|default]` аккаунт считается exhausted для модели.

Канон: [`docs/architecture/quota-reset-periods-and-account-state.md`](docs/architecture/quota-reset-periods-and-account-state.md:1).

### Persisted runtime state (last_used + quota_exhausted)
Runtime state не хранится в provider-config.

Файлы состояния:
- `secrets/<provider_id>/state/<account>/last_used_at.json`
- `secrets/<provider_id>/state/<account>/quota_exhausted/<model>.json`

Контракты:
- [`docs/contracts/state/account-last-used.schema.json`](docs/contracts/state/account-last-used.schema.json:1)
- [`docs/contracts/state/account-quota-exhausted.schema.json`](docs/contracts/state/account-quota-exhausted.schema.json:1)

### Qwen token refresh policy
Qwen refresh выполняется:
1) по idle-threshold,
2) либо по 401/403 (refresh + retry один раз).

Порог задаётся env-переменной (дефолт 180 секунд).

Состояния исчерпания в `rounding`:
- если все аккаунты во временном cooldown, прокси возвращает `all_accounts_on_cooldown`;
- если все аккаунты исчерпали quota для модели, прокси возвращает `all_accounts_exceed_quota`.

Нормативный формат `429` ошибок закреплен в [`docs/contracts/api/openai/errors/429-error.schema.json`](contracts/api/openai/errors/429-error.schema.json).

---

## 4) Vertex AI mode (опционально)

Используется сервисный аккаунт в `secrets/service_account.json` и переменные `VERTEX_PROJECT_ID`/`VERTEX_LOCATION`.

---

## ⚠️ Известные проблемы с VS Code терминалом

### Проблема: ложное прерывание скрипта
При запуске OAuth-скриптов в **интегрированном терминале VS Code** возможно ложное срабатывание `KeyboardInterrupt` (прерывание без нажатия Ctrl+C).

**Причина:** VS Code автоматически активирует Python-окружение при открытии терминала, что может прервать выполнение команд.

**Решения:**

1. **Отключить автоактивацию окружения** (рекомендуется) — создайте файл `.vscode/settings.json`:
   ```json
   {
       "python.terminal.activateEnvironment": false,
       "python.terminal.activateEnvInCurrentTerminal": false
   }
   ```

2. **Подождать активацию окружения** — откройте терминал, дождитесь автоматической активации виртуального окружения (появится `(gemini-openai-proxy)` в prompt), и только затем запускайте скрипт.

3. **Использовать системный терминал** — запускайте скрипты в обычном терминале Linux вместо VS Code integrated terminal.

---

## Важное
- Legacy-путь `USER_CREDS_PATH` больше не используется.
- Для Gemini quota multi-account `project_id` задаётся на уровне аккаунта в provider-config.

Важно: disjoint groups — каждый аккаунт может быть только в одной группе (обязательная валидация).

---

## Поведение прокси при наличии/отсутствии авторизации

- `GET /v1/models` и `GET /<group_id>/v1/models`:
  - Если в provider-config присутствует `groups`, список моделей формируется как объединение `groups.<group_id>.models` по провайдерам.
    - Примеры структуры: [`docs/examples/gemini_accounts_config.example.json`](docs/examples/gemini_accounts_config.example.json:1), [`docs/examples/qwen_accounts_config.example.json`](docs/examples/qwen_accounts_config.example.json:1).
  - Если `groups` отсутствует, используется backward-compatible поведение: список моделей формируется динамически и показывает только модели, для которых реально доступна авторизация:
    - Gemini quota модели — если валиден provider-config (`secrets/gemini_cli/accounts_config.json` по умолчанию) и есть `refresh_token` в credentials активного (или любого из `all_accounts` для `rounding`) аккаунта.
    - Qwen quota модели — если валиден provider-config (`secrets/qwen_code/accounts_config.json` по умолчанию) и есть `refresh_token` в credentials активного (или любого из `all_accounts` для `rounding`) аккаунта.
    - Vertex модели — если задан `VERTEX_PROJECT_ID` и существует `secrets/service_account.json`.

- При старте прокси выполняется fail-fast проверка: если не найден ни один валидный источник авторизации (Gemini quota / Qwen quota / Vertex), контейнер завершается с ошибкой и пишет диагностику в логи.

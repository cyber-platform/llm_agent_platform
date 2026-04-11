# 🔐 Руководство по авторизации

Платформа поддерживает несколько `LLM provider`-specific контуров авторизации:
- Gemini OAuth quota (Google Cloud Code / `gemini-cli` совместимый поток).
- Qwen OAuth quota (device flow).
- OpenAI ChatGPT OAuth runtime (Authorization Code + PKCE).

Также опционально поддерживается Vertex AI через сервисный аккаунт.

Общее устройство платформы описано в [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1), а `LLM provider`-specific особенности должны выноситься на отдельные страницы в [`docs/providers/`](docs/providers:1).

Актуальный список `LLM provider` и их readiness/status сводится в [`docs/providers/README.md`](docs/providers/README.md:1).

Для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) в текущем каноне фиксируется static catalog baseline и OAuth/runtime boundary без live discovery.

---

## 1) Gemini OAuth quota

### Что создаётся
- Базовый файл OAuth: `secrets/gemini-cli/user_credentials.json`.
- Далее пользователь может вручную переименовывать/копировать его в именованные аккаунты (например, `secrets/gemini-cli/accounts/lisa.json`, `secrets/gemini-cli/accounts/petr.json`) и указывать их в `secrets/gemini-cli/accounts_config.json`.

### Шаги
1. Установите зависимости:
   ```bash
   uv sync
   ```
2. Запустите OAuth-скрипт:
   ```bash
   uv run python scripts/get_gemini-cli_credentials.py
   ```
3. Пройдите авторизацию в браузере.

Скрипт использует loopback callback (`127.0.0.1`) и динамический порт, с ручным fallback при timeout.

Полезные переменные окружения:
- `NO_BROWSER=true` — не открывать браузер автоматически.
- `OAUTH_CALLBACK_PORT=NNNN` — фиксированный порт callback-сервера.
- `OAUTH_CALLBACK_HOST=127.0.0.1` — bind-адрес callback-сервера.
- `USER_GEMINI_CREDS_PATH=secrets/gemini-cli/user_credentials.json` — путь сохранения credentials.

---

## 2) Qwen OAuth quota

### Что создаётся
- Базовый файл OAuth: `secrets/qwen_code/user_credentials.json`.
- Далее пользователь может вручную переименовывать/копировать его в именованные аккаунты (например, `secrets/qwen_code/accounts/lisa.json`, `secrets/qwen_code/accounts/petr.json`) и указывать их в `secrets/qwen_code/accounts_config.json`.
- В credentials также сохраняется `client_id` (runtime refresh прокси использует именно его).

Текущий storage namespace для Qwen остаётся `qwen_code`; отдельная полная миграция в kebab-case вынесена в [`operational_scope/tasks/033-qwen-storage-kebab-case-migration.md`](operational_scope/tasks/033-qwen-storage-kebab-case-migration.md:1).

### Шаги
1. Запустите OAuth device-flow скрипт:
   ```bash
   uv run python scripts/get_qwen-code_credentials.py
   ```
2. Откройте ссылку в браузере и завершите подтверждение.
3. Скрипт дождётся токена и сохранит credentials в `secrets/qwen_code/user_credentials.json`.

Рекомендованный `QWEN_OAUTH_SCOPE` по parity с upstream `qwen-code`:
- `openid profile email model.completion`
- источник: `qwen-code/packages/core/src/qwen/qwenOAuth2.ts` (`QWEN_OAUTH_SCOPE`)

Важно по разделению bootstrap/runtime:
- `QWEN_OAUTH_CLIENT_ID` и `QWEN_OAUTH_SCOPE` нужны для bootstrap device-flow (скрипт [`scripts/get_qwen-code_credentials.py`](scripts/get_qwen-code_credentials.py:1)).
- Runtime прокси при refresh берёт `client_id` из credentials-файла аккаунта.

---

## 3) Конфиги ротации аккаунтов (single/rounding)

Источник политики ротации — только `LLM provider`-конфиги:
- `secrets/gemini-cli/accounts_config.json`
- `secrets/qwen_code/accounts_config.json`
- `secrets/openai-chatgpt/accounts_config.json`

Канонический общий документ по всем `LLM provider`-agnostic параметрам accounts-config:
- [`docs/configuration/provider-accounts-config.md`](docs/configuration/provider-accounts-config.md:1)

Примеры структуры вынесены в отдельные файлы:
- Gemini: [`docs/examples/gemini_accounts_config.example.json`](docs/examples/gemini_accounts_config.example.json:1)
- Qwen: [`docs/examples/qwen_accounts_config.example.json`](docs/examples/qwen_accounts_config.example.json:1)
- OpenAI ChatGPT: [`docs/examples/openai_chatgpt_accounts_config.example.json`](docs/examples/openai_chatgpt_accounts_config.example.json:1)

Для Qwen в `accounts.<name>` достаточно `credentials_path`; поле `project_id` не требуется.

### Persisted runtime state (last_used + quota_exhausted)
Runtime state не хранится в `LLM provider`-config.

С 2026-03-18 вводится отдельный runtime state контур, чтобы:

- persisted state переживал рестарт;
- state-файлы можно было хранить на HDD (много перезаписей), а `secrets/` оставались на SSD.

Канон (архитектура):

- [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)

Ключевая env-переменная:

- `STATE_DIR` — директория, где храним все state-файлы; optional, default `/app/state`.
- `STATE_FLUSH_INTERVAL_SECONDS` — интервал periodic flush async writer; default `3`.
- `STATE_WRITER_MAX_PENDING_FILES` — лимит уникальных dirty paths в coalesce map; default `1024`.

Layout:

```
<STATE_DIR>/
  <provider_id>/
    accounts/
      <account_name>/
        account_state.json
    groups/
      <group_id>/
        quota_state.json
```

`account_state.json` (per-account) содержит:

- `last_used_at`
- `cooldown.last_cooldown_at`
- `quota_exhausted.keys` (по моделям или по ключу `__provider__`)

Важно:

- чистый `select_account()` не должен обновлять `last_used_at`; это поле меняется на успешном request-path;
- если `LLM provider` не объявляет `groups`, runtime использует дефолтную логическую группу `g0`.

`quota_state.json` (per `LLM provider`-group snapshot) — файл мониторинга для администратора (только числа/доли).

Контракты:

- [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1)
- [`docs/contracts/state/group-quota-state.schema.json`](docs/contracts/state/group-quota-state.schema.json:1)

### Qwen token refresh policy
Qwen refresh выполняется:
1) по idle-threshold,
2) либо по 401/403 (refresh + retry один раз).

Порог задаётся env-переменной (дефолт 180 секунд).

Состояния исчерпания в `rounding`:
- если все аккаунты во временном cooldown, прокси возвращает `all_accounts_on_cooldown`;
- если все аккаунты исчерпали quota для модели, прокси возвращает `all_accounts_exceed_quota`.

Нормативный формат `429` ошибок закреплен в [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1).

Дополнение: теория паттерна async writer (coalesce map) вынесена в:

- [`docs/theory/coalesce-map.md`](docs/theory/coalesce-map.md:1)

---

## 4) OpenAI ChatGPT OAuth runtime

Текущий статус интеграции [`openai-chatgpt`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1):

- `GET /openai-chatgpt/v1/models` и `POST /openai-chatgpt/v1/chat/completions` уже обслуживаются runtime implementation.
- Для каталога используется static bootstrap catalog без live discovery.
- Bootstrap script реализован в [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py:1).
- `provider implementation` использует private backend surface и общий `LLM provider` accounts-config contract для `single` и `rounding`.
- Usage adapter вынесен в monitoring-only контур [`llm_agent_platform/services/provider_usage_limits.py`](llm_agent_platform/services/provider_usage_limits.py:1).

### Что создаётся
- Базовый файл OAuth по умолчанию: `secrets/openai-chatgpt/accounts/user_credentials.json`.
- Далее пользователь может переименовать или скопировать его в именованные account-файлы и сослаться на них через `OPENAI_CHATGPT_ACCOUNTS_CONFIG_PATH`.

`LLM provider`-specific канон:
- [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)

### Runtime state foundation

В `STATE_DIR` для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) канонизируется account-centric layout:

```text
<STATE_DIR>/openai-chatgpt/
  auth/oauth-account.json
  accounts/
    <account_name>/
      account_state.json
      usage_windows.json
      request_usage.json
  groups/
    <group_id>/
      quota_state.json
```

Контракты:

- OAuth state: [`docs/contracts/state/openai-chatgpt-oauth-state.schema.json`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:1)
- Routing state: [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1)
- Usage windows: [`docs/contracts/state/openai-chatgpt-usage-windows.schema.json`](docs/contracts/state/openai-chatgpt-usage-windows.schema.json:1)
- Request usage: [`docs/contracts/state/openai-chatgpt-request-usage.schema.json`](docs/contracts/state/openai-chatgpt-request-usage.schema.json:1)
- Group snapshot: [`docs/contracts/state/group-quota-state.schema.json`](docs/contracts/state/group-quota-state.schema.json:1)

`account_id` в OAuth state трактуется как optional best-effort field и должен использоваться только при наличии значения.

### Storage boundary

Для платформы в целом каноническая граница хранения задаётся так:

- user OAuth credentials в `secrets/<provider_id>/...` — это пользовательские credentials;
- общий quota state живёт только в [`STATE_DIR`](llm_agent_platform/config.py:30) по общему канону [`account_state.json`](docs/contracts/state/account-state.schema.json:1) и [`quota_state.json`](docs/contracts/state/group-quota-state.schema.json:1);
- `LLM provider`-specific usage snapshot, если `LLM provider` умеет отдавать usage/limits данные, тоже живёт только в [`STATE_DIR`](llm_agent_platform/config.py:30).

Следствие:

- `LLM provider`-specific monitoring snapshot не должен перетирать `access_token`, `refresh_token` и другой OAuth material в `secrets/`;
- `LLM provider`-specific mutable state и monitoring state должны быть структурно отделены от пользовательских credentials.

### Current admin monitoring boundary

Для текущего monitoring PoC admin surface допустима без auth только в local single-user boundary.

Это временное допущение для operator-facing PoC и не считается baseline для shared dev or prod. Future hardening вынесен в [`operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md`](operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md:1).

### Path resolution ports

Чтобы эта граница не размазывалась по `provider implementation`, path-resolution должен быть разделён на два платформенных направления:

- credentials locator port — отвечает только за ссылки на user credentials в `secrets/`;
- runtime state paths port — отвечает только за mutable state в [`STATE_DIR`](llm_agent_platform/config.py:30), включая platform router/quota state и `LLM provider` monitoring snapshots.

Это означает, что `provider implementation` и usage-monitoring не должны сами вычислять пути строковыми `replace(...)`, а должны опираться на общие платформенные path-resolver компоненты.

Runtime invariant для `LLM provider`:
- `one forced refresh retry on auth failure`

### Что запускать

1. Получить OAuth state:
   ```bash
   uv run python scripts/get_openai-chatgpt_credentials.py
   ```
2. Указать файл аккаунта в `OPENAI_CHATGPT_ACCOUNTS_CONFIG_PATH`.
3. Для single mode достаточно одного аккаунта с `credentials_path`; для rounding `LLM provider` использует тот же общий quota contour, что и остальные `LLM provider`.

Пример `LLM provider` accounts-config:
- [`docs/examples/openai_chatgpt_accounts_config.example.json`](docs/examples/openai_chatgpt_accounts_config.example.json:1)

---

## 5) Vertex AI mode (опционально)

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
- Для Gemini quota multi-account `project_id` задаётся на уровне аккаунта в `LLM provider`-config.

Важно: disjoint groups — каждый аккаунт может быть только в одной группе (обязательная валидация).

---

## Поведение платформы при наличии/отсутствии авторизации

- `GET /<provider_name>/v1/models` и `GET /<provider_name>/<group_id>/v1/models` работают внутри выбранного `LLM provider` namespace.
- Если `LLM provider` поддерживает groups, список моделей для named group фильтруется по `groups.<group_id>.models` данного `LLM provider`.
- Если groups не заданы, используется default group выбранного `LLM provider`.

- При старте прокси выполняется fail-fast проверка: если не найден ни один валидный источник авторизации (Gemini quota / Qwen quota / Vertex), контейнер завершается с ошибкой и пишет диагностику в логи.

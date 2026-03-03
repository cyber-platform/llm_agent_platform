# 🔐 Руководство по авторизации

Прокси поддерживает два независимых контура авторизации:
- Gemini OAuth quota (Google Cloud Code / `gemini-cli` совместимый поток).
- Qwen OAuth quota (device flow).

Также опционально поддерживается Vertex AI через сервисный аккаунт.

---

## 1) Gemini OAuth quota

### Что создаётся
- Базовый файл OAuth: `secrets/user_gemini_credentials.json`.
- Далее пользователь может вручную переименовывать/копировать его в именованные аккаунты (например, `secrets/gemini_lisa.json`, `secrets/gemini_petr.json`) и указывать их в `gemini_accounts_config.json`.

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
- `USER_GEMINI_CREDS_PATH=secrets/user_gemini_credentials.json` — путь сохранения credentials.

---

## 2) Qwen OAuth quota

### Что создаётся
- Базовый файл OAuth: `secrets/user_qwen_credentials.json`.
- Далее пользователь может вручную переименовывать/копировать его в именованные аккаунты (например, `secrets/qwen_lisa.json`, `secrets/qwen_petr.json`) и указывать их в `qwen_accounts_config.json`.
- В credentials также сохраняется `client_id` (для стабильного refresh даже при изменении env-конфига).

### Шаги
1. Запустите OAuth device-flow скрипт:
   ```bash
   uv run python scripts/get_qwen_oauth_credentials.py
   ```
2. Откройте ссылку в браузере и завершите подтверждение.
3. Скрипт дождётся токена и сохранит credentials в `secrets/user_qwen_credentials.json`.

Рекомендованный `QWEN_OAUTH_SCOPE` по parity с upstream `qwen-code`:
- `openid profile email model.completion`
- источник: `qwen-code/packages/core/src/qwen/qwenOAuth2.ts` (`QWEN_OAUTH_SCOPE`)

---

## 3) Конфиги ротации аккаунтов (single/rounding)

Источник политики ротации — только provider-конфиги:
- `secrets/gemini_accounts_config.json`
- `secrets/qwen_accounts_config.json`

Примеры структуры вынесены в отдельные файлы:
- Gemini: `docs/examples/gemini_accounts_config.example.json`
- Qwen: `docs/examples/qwen_accounts_config.example.json`

Для Qwen в `accounts.<name>` достаточно `credentials_path`; поле `project_id` не требуется.

Режимы:
- `single` — используется только `active_account`.
- `rounding` — round-robin по `all_accounts` с раздельной обработкой `rate_limit` (cooldown) и `quota_exhausted` (exhausted-until).

Состояния исчерпания в `rounding`:
- если все аккаунты во временном cooldown, прокси возвращает `all_accounts_on_cooldown`;
- если все аккаунты исчерпали quota для модели, прокси возвращает `all_accounts_exceed_quota`.

Нормативный формат `429` ошибок закреплен в [`docs/contracts/api/openai/errors/429-error.schema.json`](contracts/api/openai/errors/429-error.schema.json).

---

## 4) Vertex AI mode (опционально)

Используется сервисный аккаунт в `secrets/service_account.json` и переменные `VERTEX_PROJECT_ID`/`VERTEX_LOCATION`.

---

## Важное
- Legacy-путь `USER_CREDS_PATH` больше не используется.
- Для Gemini quota multi-account `project_id` задаётся на уровне аккаунта в `gemini_accounts_config.json`.

---

## Поведение прокси при наличии/отсутствии авторизации

- `/v1/models` теперь формируется динамически и показывает только модели, для которых реально доступна авторизация:
  - Gemini quota модели — если валиден `gemini_accounts_config.json` и есть `refresh_token` в credentials активного (или любого из `all_accounts` для `rounding`) аккаунта.
  - Qwen quota модели — если валиден `qwen_accounts_config.json` и есть `refresh_token` в credentials активного (или любого из `all_accounts` для `rounding`) аккаунта.
  - Vertex модели — если задан `VERTEX_PROJECT_ID` и существует `secrets/service_account.json`.

- При старте прокси выполняется fail-fast проверка: если не найден ни один валидный источник авторизации (Gemini quota / Qwen quota / Vertex), контейнер завершается с ошибкой и пишет диагностику в логи.

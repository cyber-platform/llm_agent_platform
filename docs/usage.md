# 🚀 Использование и возможности

Прокси-сервер предоставляет два режима работы: **OpenAI Compatible API** и **Native Gemini API**, что позволяет легко интегрировать Gemini 3 в любые инструменты разработки.

---

## 🔌 Подключение к IDE

### Вариант 1: OpenAI Compatible (Рекомендуемый)
Подходит для большинства инструментов (VS Code, Cursor, Cline, Roo Code и др.), которые поддерживают OpenAI API.

| Параметр | Значение |
| :--- | :--- |
| **API Provider** | `OpenAI Compatible` |
| **Base URL** | `http://localhost:4000/v1` |
| **API Key** | `any-string` (например, `sk-proxy`) |
| **Model ID** | Выберите из списка ниже (например, `gemini-3-flash-preview-quota`) |

> **Примечание:** В этом режиме прокси автоматически исправляет ошибки валидации `thought_signature` для Gemini 3, обеспечивая стабильную работу даже в клиентах, которые официально не поддерживают этот протокол.

### Вариант 2: Native Gemini (Для Kilo Code и др.)
Подходит для инструментов, которые имеют встроенную поддержку Google Gemini (Google AI Studio / Vertex AI) и позволяют изменить Base URL.

| Параметр | Значение |
| :--- | :--- |
| **API Provider** | `Gemini` (или `Google Vertex AI`) |
| **Base URL** | `http://localhost:4000` (без `/v1`) |
| **API Key** | `any-string` |
| **Model ID** | `gemini-3-flash-preview` (или другая) |

> **Важно:** В этом режиме клиент сам формирует запросы в формате Gemini. Прокси выступает как прозрачный шлюз, добавляя только авторизацию.

---

## 🤖 Доступные модели

Прокси поддерживает динамическое переключение режимов оплаты через суффикс в названии модели.

### Группа Quota (Персональные квоты)
Использует лимиты вашей подписки `Google AI Pro` или `Free tier`. Рекомендуется для большинства задач.
*   `gemini-3.1-pro-preview-quota` — Максимальный интеллект.
*   `gemini-3-flash-preview-quota` — Высокая скорость и большой контекст.
*   `gemini-2.5-pro-quota` — Стабильная Pro-модель.
*   `gemini-2.5-flash-quota` — Оптимальный баланс.
*   `gemini-2.5-flash-lite-quota` — Максимальная экономия.
*   `qwen-coder-model-quota` — Qwen quota-модель (OAuth), маппится в upstream `coder-model`.

### Ротация quota-аккаунтов
Для quota-провайдеров поддерживаются режимы `single` и `rounding`.

- `single`: используется только `active_account`.
- `rounding`: round-robin по `all_accounts` с раздельной обработкой `rate_limit` (cooldown) и `quota_exhausted` (exhausted-until).
- Опции `rotation_policy` для `rounding`:
  - `random_order`: случайный выбор следующего аккаунта из доступных.
  - `rotate_after_n_successes`: принудительное переключение после N успешных запросов.
- Если все аккаунты во временном cooldown, возвращается `all_accounts_on_cooldown`.
- Если все аккаунты исчерпали quota для модели, возвращается `all_accounts_exceed_quota`.
- Нормативный формат `429` ошибок: [`docs/contracts/api/openai/errors/429-error.schema.json`](contracts/api/openai/errors/429-error.schema.json).

Quota groups (URL-prefix):
- Можно использовать префикс группы в пути: `/<group_id>/v1/*`.
- `GET /v1/models` и `GET /<group_id>/v1/models` становятся group-aware: при наличии `groups` в provider-config модели берутся из `groups.<group_id>.models`.

Конфиги и примеры структуры:
- рабочие файлы (рекомендованный layout provider-scoped):
  - `secrets/gemini_cli/accounts_config.json`
  - `secrets/qwen_code/accounts_config.json`
- примеры: [`docs/examples/gemini_accounts_config.example.json`](docs/examples/gemini_accounts_config.example.json:1), [`docs/examples/qwen_accounts_config.example.json`](docs/examples/qwen_accounts_config.example.json:1)

Важно: `model_quota_resets` теперь задаёт **период восстановления квоты** (формат `DD:HH:MM`), см. [`docs/architecture/quota-reset-periods-and-account-state.md`](docs/architecture/quota-reset-periods-and-account-state.md:1).

### Группа Vertex (Облачные кредиты)
Использует баланс вашего Google Cloud проекта ($10/мес кредитов для Pro-пользователей).
*   `gemini-3.1-pro-preview-vertex`
*   `gemini-3-flash-preview-vertex`
*   `gemini-2.5-pro-vertex`
*   `gemini-2.5-flash-vertex`

### Специализированные
*   `nano-banana` — Модель, оптимизированная для работы с изображениями.

---

## ✨ Ключевые функции

### 🧠 Режим рассуждений (Reasoning)
Прокси автоматически извлекает "мысли" модели Gemini и передает их в формате `reasoning_content`. В интерфейсе Kilo Code вы увидите процесс размышления модели перед основным ответом.

### 🖼️ Работа с изображениями (Vision)
Вы можете прикреплять скриншоты или фотографии к вашим запросам. Прокси корректно транслирует `image_url` в нативный формат Gemini.

### 🛠️ Вызов инструментов (Function Calling)
Полная поддержка Native Tool Calling. Модель может:
*   Читать и записывать файлы.
*   Выполнять команды в терминале.
*   Использовать MCP-серверы.

---

## 📸 Скриншоты работы

тут будут скриншоты работы с kilo code

---

## 📊 Мониторинг квот

Для наглядного контроля остатка ваших лимитов по квотам рекомендуется использовать официальное приложение **gemini-cli**.

1.  **Установка и авторизация**:
    Установите `gemini-cli` и пройдите авторизацию через ваш Google-аккаунт:
    ```bash
    # Внутри gemini-cli
    /auth
    ```
    Выберите способ авторизации через Google аккаунт.

2.  **Просмотр статистики**:
    После этого вы сможете вызывать слеш-команду `/stats` прямо в терминале `gemini-cli`, чтобы увидеть остаток вашей дневной квоты в процентах.

📸 *Скриншот статистики из gemini-cli*

---

## 💡 Советы по использованию
1.  **Экономия токенов**: Используйте модели `flash-lite` для простых задач или первичного анализа кода.
2.  **Контекст**: Gemini 3 поддерживает огромные окна контекста. Прокси корректно передает информацию об использовании токенов (`usage`), чтобы вы могли контролировать расход квот в вашей IDE.

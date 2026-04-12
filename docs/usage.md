# 🚀 Использование платформы

Платформа предоставляет provider-centric OpenAI-compatible API и отдельные provider-specific integrations.

---

## 🔌 Подключение к IDE

### Вариант 1: OpenAI Compatible
Подходит для большинства инструментов, которые умеют работать с OpenAI API.

| Параметр | Значение |
| :--- | :--- |
| **API Provider** | `OpenAI Compatible` |
| **Base URL** | `http://localhost:4000/<provider_name>/v1` |
| **API Key** | `any-string` (например, `sk-proxy`) |
| **Model ID** | Выберите модель из каталога выбранного provider |

Примеры base URL:
- `http://localhost:4000/gemini-cli/v1`
- `http://localhost:4000/qwen-code/v1`
- `http://localhost:4000/google-vertex/v1`
- `http://localhost:4000/openai-chatgpt/v1`

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

## 🤖 Каталоги моделей

Платформа использует provider-local catalogs.

Ключевые правила:
- модель выбирается внутри каталога выбранного provider;
- одинаковые `model_id` у разных providers допустимы;
- публичные model ids не должны кодировать transport semantics через suffix `quota` или `vertex`.

Provider-specific особенности каталогов должны быть описаны на отдельных страницах в [`docs/providers/`](docs/providers:1).

Актуальный список providers и их catalog/runtime status сводится в [`docs/providers/index.md`](docs/providers/index.md:1).

### Ротация quota-аккаунтов
Для quota-based providers поддерживаются режимы `single` и `rounding`.

- `single`: используется только `active_account`.
- `rounding`: round-robin по `all_accounts` с раздельной обработкой `rate_limit` (cooldown) и `quota_exhausted` (exhausted-until).
- Опции `rotation_policy` для `rounding`:
  - `random_order`: случайный выбор следующего аккаунта из доступных.
  - `rotate_after_n_successes`: принудительное переключение после N успешных запросов.
- Если все аккаунты во временном cooldown, возвращается `all_accounts_on_cooldown`.
- Если все аккаунты исчерпали quota для модели, возвращается `all_accounts_exceed_quota`.
- Нормативный формат `429` ошибок: [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1).

Quota groups:
- Группа адресуется только внутри provider namespace: `/<provider_name>/<group_id>/v1/*`.
- Default group адресуется как `/<provider_name>/v1/*`.
- `GET /<provider_name>/<group_id>/v1/models` использует только provider-local group models.

Конфиги и примеры структуры:
- рабочие файлы (рекомендованный layout provider-scoped):
  - `secrets/gemini-cli/accounts_config.json`
  - `secrets/qwen_code/accounts_config.json`
- примеры: [`docs/examples/gemini_accounts_config.example.json`](docs/examples/gemini_accounts_config.example.json:1), [`docs/examples/qwen_accounts_config.example.json`](docs/examples/qwen_accounts_config.example.json:1)

Важно: `model_quota_resets` теперь задаёт **период восстановления квоты** (формат `DD:HH:MM`), см. [`docs/architecture/quota-reset-periods-and-account-state.md`](docs/architecture/quota-reset-periods-and-account-state.md:1).

### Provider-specific страницы
- [`docs/providers/index.md`](docs/providers/index.md:1)
- [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)

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

## 💡 Советы по использованию
1. Выбирайте provider через base URL, а не через naming conventions модели.
2. Проверяйте provider-local `/models` перед подключением клиента.
3. Для provider-specific ограничений опирайтесь на страницы в [`docs/providers/`](docs/providers:1).

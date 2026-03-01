# System Patterns

## Архитектурные принципы
- **Разделение ответственности**: API маршруты отделены от логики трансформации данных и аутентификации.
- **Эмуляция**: Прокси должен максимально точно имитировать поведение OpenAI API, скрывая детали реализации Gemini.
- **Гибридность**: Поддержка двух режимов (Quota и Vertex) через единый интерфейс.

## Ключевые паттерны
- **Blueprint (Flask)**: Организация маршрутов по функциональным модулям (`api/openai`, `api/gemini`).
- **Transformation Layer**: Изолированная логика маппинга сообщений и инструментов (`api/openai/transform.py`).
- **Background Refresh**: Фоновое обновление OAuth токенов для минимизации задержек при запросах.
- **Quota-first Transport Parity**: Единый transport-модуль для quota-трафика с контрактом запроса, максимально близким к `gemini-cli` (`model`, `project`, `user_prompt_id`, `request.session_id`).
- **Golden Parity Validation**: Двухконтурная верификация parity через runtime capture-relay и статический эталон по коду `gemini-cli` с последующим сравнением payload в автотестах.
- **Unified Quota Account Router**: Провайдер-агностичный роутер аккаунтов для quota-контуров `gemini`/`qwen` с режимами `single`/`rounding`, switch после 2 подряд quota-limit ошибок и явным состоянием `all_accounts_exceed_quota`.
- **Provider-specific Credentials Paths**: Разделение OAuth credentials по провайдерам (`USER_GEMINI_CREDS_PATH`, `USER_QWEN_CREDS_PATH`) и отдельные provider-config файлы аккаунтов (`gemini_accounts_config.json`, `qwen_accounts_config.json`).

## Структура проекта
- `api/`: Эндпоинты и логика обработки запросов.
- `auth/`: Управление учетными данными и токенами.
- `core/`: Общие модели, утилиты и маппинги.
- `docs/`: Документация проекта.
- `secrets/`: (Игнорируется Git) Хранение чувствительных данных.

# Архитектурный план: Гибридный Gemini Proxy (Эмуляция Gemini CLI)

Этот документ описывает финальную архитектуру локального прокси-сервера для работы с моделями Google Gemini.
Система реализована на чистом Python (Flask + httpx) и полностью эмулирует поведение официального `gemini-cli` для доступа к расширенным квотам подписки Google AI Pro (1500+ запросов/день).

## 1. Обзор архитектуры

Система разворачивается как Docker-контейнер, экспортирующий OpenAI-совместимый API на порту `4000`.

### Компоненты
1.  **Proxy Server (Flask)**: Принимает запросы в формате OpenAI (`/v1/chat/completions`). Реализует "умный" стриминг с поддержкой `stream_options` для Kilo Code.
2.  **Auth Adapter (OAuth 2.0)**: Фоновый процесс, обновляющий токены вашего личного аккаунта, используя официальный Client ID от `gemini-cli`.
3.  **Project Discovery**: Модуль автоматического обнаружения "скрытого" проекта Cloud Code, необходимого для активации пользовательских квот.
4.  **Dual-Mode Engine**:
    *   **Quota Mode**: Направляет запросы в `cloudcode-pa.googleapis.com` (как это делает VS Code расширение), расходуя личную квоту пользователя.
    *   **Vertex Mode**: Направляет запросы в `aiplatform.googleapis.com`, расходуя платные кредиты ($10/мес) через Service Account.

## 2. Профили моделей (Model IDs)

Система поддерживает динамическое переключение между режимами оплаты через суффикс модели:

### Группа Quota (Бесплатно / 1500 req/day)
Использует вашу личную подписку Google AI Pro.
*   `gemini-3-pro-preview-quota`
*   `gemini-3-flash-preview-quota`
*   `gemini-2.5-pro-quota`
*   `gemini-2.5-flash-quota`

### Группа Vertex (Платные кредиты / $10/mo)
Использует баланс облачного проекта.
*   `gemini-3-pro-preview-vertex`
*   `gemini-3-flash-preview-vertex`
*   `gemini-2.5-pro-vertex`
*   `gemini-2.5-flash-vertex`

## 3. Структура проекта

```text
gemini-openai-proxy/
├── Dockerfile               # Сборка образа
├── docker-compose.yml       # Запуск контейнера
├── main.py                  # Код прокси-сервера (Flask)
├── requirements.txt         # Зависимости Python
├── scripts/
│   └── get_oauth_credentials.py # Скрипт авторизации (эмуляция Gemini CLI)
└── secrets/                 # Директория для ключей (в .gitignore)
    ├── user_credentials.json # Токены OAuth (создаются скриптом)
    └── service_account.json # Ключ Vertex AI (опционально)
```

## 4. Инструкция по эксплуатации

### Первоначальная настройка
1.  Следуйте [Credentials Setup Guide](./Credentials_Setup_Guide.md) для получения ключей.
2.  Запустите скрипт авторизации: `python3 scripts/get_oauth_credentials.py`.
    *   Это откроет браузер для входа в Google.
    *   Скрипт сохранит токены, притворившись официальным приложением Gemini CLI.
3.  (Опционально) Положите `service_account.json` в папку `secrets/` для доступа к платным кредитам.

### Запуск
```bash
docker-compose up -d --build
```

### Подключение IDE (Kilo Code / Cursor)
*   **Provider**: OpenAI Compatible
*   **Base URL**: `http://localhost:4000/v1`
*   **API Key**: Любой (например, `sk-proxy`)
*   **Model**: Выберите любой ID из списка в разделе 2 (например, `gemini-3-flash-preview-quota`).

## 5. Почему это работает
Обычные API ключи Google AI Studio имеют жесткие лимиты для бесплатных аккаунтов. Однако Google предоставляет расширенные квоты для пользователей своих IDE-расширений (Cloud Code).
Наш прокси использует тот же `Client ID` и тот же API-эндпоинт (`cloudcode-pa`), что и официальные инструменты, заставляя Google считать наши запросы легитимным трафиком разработчика с подпиской Pro.
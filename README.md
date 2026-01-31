# 🚀 Gemini Hybrid OpenAI Proxy (Gemini CLI Emulation)

Легкий и мощный гибридный прокси-сервер для Google Gemini, который превращает вашу подписку **Google AI Pro** в полноценный инструмент для разработки.

Этот шлюз **полностью эмулирует поведение `gemini-cli`**, используя официальные Client ID и Secret от Google Cloud Code. Это позволяет получить доступ к расширенным пользовательским квотам (1500+ запросов/день), которые недоступны через стандартные API-ключи AI Studio.

## ✨ Ключевые возможности

*   **🔒 Эмуляция Gemini CLI**: Использует те же механизмы авторизации, что и официальный инструмент, гарантируя доступ к "User Quota" вместо ограниченной "Project Quota" (20 req/day).
*   **🔄 Автоматический OAuth**: Шлюз сам поддерживает сессию живой, обновляя токены в фоновом режиме.
*   **💎 Доступ к квотам Pro**: Используйте расширенные лимиты вашей подписки (Tier 1) прямо в редакторе кода.
*   **🌓 Гибридная модель оплаты**:
    *   `gemini-*-quota`: Использует ваши личные бесплатные квоты через эмуляцию Cloud Code API.
    *   `gemini-*-vertex`: Использует облачные кредиты ($10/мес), входящие в подписку, через Vertex AI API.
*   **⚡ Прямой HTTP-движок**: Никаких лишних SDK. Максимальная скорость и надежность за счет прямого общения с Google API.
*   **🤖 Полная совместимость с Kilo Code (v5.2.2+)**:
    *   Поддержка `stream_options` и `usage` для отображения статистики токенов.
    *   **Поддержка инструментов (Function Calling)**: Прокси корректно обрабатывает вызовы инструментов (native tool calling), конвертируя их между форматами OpenAI и Gemini.
    *   **Автоматическая адаптация схем**: Исправляет несовместимости в JSON Schema (например, `type: ["string", "null"]`) для корректной работы с Gemini API.
*   **📦 Docker + UV**: Современная упаковка с гарантированной воспроизводимостью зависимостей.

## 🛠️ Быстрый старт

### 1. Подготовка ключей
Следуйте подробному **[Руководству по настройке ключей](./docs/Credentials_Setup_Guide.md)**.
Вам больше **не нужно** создавать свой проект в Google Cloud Console. Просто запустите скрипт:
```bash
python3 scripts/get_oauth_credentials.py
```

### 2. Настройка окружения
```bash
cp .env.example .env
# Отредактируйте .env (VERTEX_PROJECT_ID нужен только для режима Vertex)
```

### 3. Запуск
```bash
docker-compose up -d --build
```

## 🔌 Подключение к IDE (Kilo Code / Cursor / VS Code)

| Параметр | Значение |
| :--- | :--- |
| **Base URL** | `http://localhost:4000/v1` |
| **API Key** | Любое значение (например `sk-proxy`) |
| **Provider** | OpenAI Compatible |

### Особенности работы с Kilo Code:
Наш прокси специально оптимизирован для Kilo Code (включая версии v5.2.2 и новее). Он поддерживает:
*   **Подсчет токенов**: Передает `usage` в стриме, чтобы вы видели расход квот.
*   **Инструменты (Tools)**: Позволяет Kilo Code выполнять команды, читать файлы и использовать другие возможности через нативный механизм вызова функций (Native Tool Calling).
*   **Форматирование ошибок**: Ошибки Google API транслируются в формат OpenAI для корректного отображения в IDE.

### Использование в Python (LangChain / OpenAI SDK)
Прокси полностью совместим со стандартными библиотеками, включая поддержку Function Calling:
```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:4000/v1", api_key="sk-proxy")

# Простой чат
response = client.chat.completions.create(
    model="gemini-3-flash-preview-quota",
    messages=[{"role": "user", "content": "Hello!"}]
)

# Использование инструментов (Function Calling)
tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {"type": "string"}
            },
            "required": ["location"]
        }
    }
}]

response_with_tools = client.chat.completions.create(
    model="gemini-3-flash-preview-quota",
    messages=[{"role": "user", "content": "Weather in Paris?"}],
    tools=tools
)
```

### Популярные модели (Model IDs):
*   `gemini-3-pro-preview-quota` — Максимальный интеллект (Pro подписка).
*   `gemini-3-flash-preview-quota` — Молниеносная скорость.
*   `gemini-2.5-flash-lite-quota` — Экономия контекста.
*   `nano-banana` — Генерация изображений.

## 🧪 Тестирование
```bash
curl -X POST http://localhost:4000/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{"model": "gemini-3-flash-preview-quota", "messages": [{"role": "user", "content": "Привет!"}]}'
```

## 🏗️ Архитектура
Проект построен на базе **Python 3.11** и **Flask**. 
*   **Quota Mode**: Запросы идут на `cloudcode-pa.googleapis.com` с токеном пользователя.
*   **Vertex Mode**: Запросы идут на `aiplatform.googleapis.com` с токеном сервисного аккаунта.

---
Разработано с ❤️ для эффективного AI-кодинга.
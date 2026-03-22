# 🛠️ Установка и развертывание

Платформа использует **uv** и **Docker** для локального запуска и контейнерного развертывания.

Актуальные сценарии запуска сервиса вынесены в отдельный раздел [`docs/run/README.md`](docs/run/README.md:1).

Текущий основной workflow разработки:

- [`docs/run/dev.md`](docs/run/dev.md:1)

---

## 1. Предварительные требования

Перед началом убедитесь, что у вас установлены:
*   **Python 3.13+**
*   **uv** (рекомендуется для управления зависимостями)
*   **Docker** и **Docker Compose**

---

## 2. Пошаговая установка

### Шаг 1: Клонирование репозитория
```bash
git clone <your-repo-url>
cd model_proxy
```

### Шаг 2: Подготовка окружения
Используйте `uv` для автоматической настройки виртуального окружения и установки всех необходимых библиотек:
```bash
uv sync
```

### Шаг 3: Настройка конфигурации
Создайте файл `.env` на основе примера:
```bash
cp .env.example .env
```
Отредактируйте `.env`:
*   `VERTEX_PROJECT_ID`: ID вашего проекта в Google Cloud (обязательно для Vertex Mode).
*   `VERTEX_LOCATION`: Регион (по умолчанию `us-central1`).

### Шаг 4: Авторизация
Для quota-based providers подготовьте OAuth credentials. Базовый пример для Gemini OAuth:
```bash
uv run python scripts/get_gemini-cli_credentials.py
```
Подробности:
- [`docs/auth.md`](docs/auth.md:1)
- provider-specific страницы в [`docs/providers/`](docs/providers:1)

---

## 3. Запуск сервера

### Вариант А: Через Docker (рекомендуется)
Это самый простой способ запустить прокси со всеми зависимостями в изолированной среде:
```bash
docker-compose up -d --build
```
Сервер будет доступен по адресу: `http://localhost:4000`

### Вариант Б: Локальный запуск
Если вы хотите запустить сервер напрямую:
```bash
uv run python -m llm_agent_platform
```

---

## 4. Проверка работоспособности

Вы можете проверить, что сервис отвечает, через provider-scoped маршруты:

**Список моделей:**
```bash
curl http://localhost:4000/gemini-cli/v1/models
```

**Простой запрос к модели:**
```bash
curl -X POST http://localhost:4000/gemini-cli/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
  "model": "gemini-2.5-flash",
  "messages": [{"role": "user", "content": "Привет! Как дела?"}]
}'
```

---

## 📂 Структура папок
*   `llm_agent_platform/`: runtime-код платформы.
*   `scripts/`: Вспомогательные скрипты для регистрации и тестов.
*   `secrets/`: чувствительные данные и локальные credentials.
*   `docs/`: Source of Truth для архитектуры, contracts и testing traceability.

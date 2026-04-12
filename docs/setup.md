# Установка и развертывание

Платформа в первую очередь ориентирована на запуск через готовые Docker Hub образы. Локальная сборка и прямой service-local запуск остаются дополнительными сценариями для разработки.

Актуальные сценарии запуска сервиса вынесены в отдельный раздел [`docs/run/index.md`](docs/run/index.md:1).

Текущий основной workflow разработки:

- [`docs/run/dev.md`](docs/run/dev.md:1)

---

## 1. Предварительные требования

Для основного сценария достаточно:
- **Docker** и **Docker Compose**

Дополнительно для service-local разработки:
- **Python 3.13+**
- **uv**

---

## 2. Пошаговая установка

### Шаг 1: Клонирование репозитория
```bash
git clone <your-repo-url>
cd llm_agent_platform
```

### Шаг 2: Настройка конфигурации
Создайте root `.env` на основе примера:
```bash
cp .env.example .env
```
Отредактируйте `.env`:
- `VERTEX_PROJECT_ID`: ID вашего проекта в Google Cloud.
- `VERTEX_LOCATION`: Регион (по умолчанию `us-central1`).
- `GEMINI_CLI_CLIENT_ID` и `GEMINI_CLI_CLIENT_SECRET`: OAuth client для quota-based Gemini workflow.
- `DOCKERHUB_NAMESPACE`, `BACKEND_IMAGE_TAG`, `FRONTEND_IMAGE_TAG`: опциональные override-переменные только для `docker-compose-dev.yml`; по умолчанию dev compose использует `local/llm-agent-platform-backend:dev` и `local/llm-agent-platform-frontend:dev`.

### Шаг 3: Авторизация
Для quota-based providers подготовьте OAuth credentials. Базовый пример для Gemini OAuth:
```bash
uv run --project services/backend python services/backend/scripts/get_gemini-cli_credentials.py
```
Подробности:
- [`docs/auth.md`](docs/auth.md:1)
- provider-specific страницы в [`docs/providers/`](docs/providers:1)

---

## 3. Запуск сервисов

### Основной сценарий: запуск через готовые Docker Hub образы
Это рекомендуемый путь для первого старта и reproducible runtime. `docker-compose.yml` не собирает сервисы локально, а сразу скачивает опубликованные release images из Docker Hub:
```bash
docker compose up -d
```
Используются следующие образы:
- `docker.io/medphisiker/llm-agent-platform-backend:v0.0.1`
- `docker.io/medphisiker/llm-agent-platform-frontend:v0.0.1`

Сервисы будут доступны по адресам:
- backend: `http://127.0.0.1:4000`
- frontend: `http://127.0.0.1:4173`

### Дополнительный сценарий: локальная docker-сборка для разработки
Если нужно собрать текущие локальные исходники в контейнеры, используйте `docker-compose-dev.yml`. Этот сценарий тоже не требует `uv`, потому что backend и frontend собираются внутри Docker:
```bash
docker compose -f docker-compose-dev.yml up --build -d
```
По умолчанию будут собраны локальные образы:
- `local/llm-agent-platform-backend:dev`
- `local/llm-agent-platform-frontend:dev`

### Service-local запуск без Docker
Если нужно запускать отдельные сервисы вне Compose, используйте их service-local workflow. Например, backend запускается напрямую так:
```bash
uv run --project services/backend python -m llm_agent_platform
```

Архитектурные границы сервисов и дальнейшая навигация по service-specific документации описаны в [`docs/architecture/system-overview.md`](docs/architecture/system-overview.md:1).

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

## Структура папок
- `services/backend/llm_agent_platform/`: runtime-код backend сервиса.
- `services/backend/scripts/`: bootstrap-скрипты для OAuth и service-local tooling.
- `services/frontend/`: React frontend и Docker image для локального UI.
- `secrets/`: чувствительные данные и локальные credentials.
- `docs/`: Source of Truth для архитектуры, contracts и testing traceability.

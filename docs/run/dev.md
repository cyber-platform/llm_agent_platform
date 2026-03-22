# Dev run

## Назначение

Текущий Docker-сценарий проекта — это dev-container модель:

- образ контейнера отвечает только за среду выполнения
- код приложения монтируется с хоста
- изменение логики в [`llm_agent_platform/`](llm_agent_platform:1) не требует rebuild образа

Канонические runtime файлы:

- [`Dockerfile`](Dockerfile:1)
- [`docker-compose.yml`](docker-compose.yml:1)

## Dev container model

В текущем каноне:

- в образ ставятся Python, `uv` и зависимости из [`pyproject.toml`](pyproject.toml:1) и [`uv.lock`](uv.lock:1)
- код приложения не baked-in в image
- runtime-код приходит через bind-mount [`./llm_agent_platform:/app/llm_agent_platform`](docker-compose.yml:9)

Следствие:

- изменение кода в [`llm_agent_platform/`](llm_agent_platform:1) → достаточно restart контейнера
- изменение зависимостей, версии Python, `uv`, [`pyproject.toml`](pyproject.toml:1) или [`uv.lock`](uv.lock:1) → нужен rebuild образа

## Первый запуск после изменения среды

Если изменился [`Dockerfile`](Dockerfile:1), [`docker-compose.yml`](docker-compose.yml:1), [`pyproject.toml`](pyproject.toml:1) или [`uv.lock`](uv.lock:1), запускайте:

```bash
docker compose up -d --build
```

## Обычный цикл разработки

Если изменился только код в [`llm_agent_platform/`](llm_agent_platform:1), достаточно:

```bash
docker compose restart model-proxy
```

## Что именно смонтировано

Основные bind-mounts в [`docker-compose.yml`](docker-compose.yml:7):

- [`./llm_agent_platform:/app/llm_agent_platform`](docker-compose.yml:9)
- [`./pyproject.toml:/app/pyproject.toml`](docker-compose.yml:11)
- [`./uv.lock:/app/uv.lock`](docker-compose.yml:12)
- [`./secrets:/app/secrets`](docker-compose.yml:16)

Отдельно также монтируются внешние runtime директории для state и logs.

## Что пока не входит в scope

- автоматический hot reload без restart контейнера
- production deployment scenario

Для production запусков зарезервирована страница [`docs/run/prod.md`](docs/run/prod.md:1).

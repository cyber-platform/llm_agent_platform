# Dev run

## Назначение

Текущий Docker-сценарий проекта — это dev-container модель:

- образ контейнера отвечает только за среду выполнения
- код приложения монтируется с хоста
- изменение логики в [`services/backend/llm_agent_platform/`](services/backend/llm_agent_platform:1) не требует rebuild образа

Канонические runtime файлы:

- [`services/backend/Dockerfile`](services/backend/Dockerfile:1)
- [`docker-compose.yml`](docker-compose.yml:1)
- [`docker-compose-dev.yml`](docker-compose-dev.yml:1)

## Dev container model

В текущем каноне:

- в образ ставятся Python, `uv` и зависимости из [`services/backend/pyproject.toml`](services/backend/pyproject.toml:1) и [`services/backend/uv.lock`](services/backend/uv.lock:1)
- код приложения не baked-in в image
- runtime-код приходит через bind-mount [`./services/backend/llm_agent_platform:/app/llm_agent_platform`](docker-compose.yml:9)

Следствие:

- изменение кода в [`services/backend/llm_agent_platform/`](services/backend/llm_agent_platform:1) → достаточно restart контейнера
- изменение зависимостей, версии Python, `uv`, [`services/backend/pyproject.toml`](services/backend/pyproject.toml:1) или [`services/backend/uv.lock`](services/backend/uv.lock:1) → нужен rebuild образа

## Первый запуск после изменения среды

Если изменился [`services/backend/Dockerfile`](services/backend/Dockerfile:1), [`docker-compose.yml`](docker-compose.yml:1), [`services/backend/pyproject.toml`](services/backend/pyproject.toml:1) или [`services/backend/uv.lock`](services/backend/uv.lock:1), запускайте:

```bash
docker compose up -d --build
```

Для текущего mini-release с login flow через `user_service` основной assembled dev contour поднимается через:

```bash
docker compose -f docker-compose-dev.yml up -d --build
```

После первого старта `user_service` на fresh database нужно применить миграции:

```bash
docker exec user-service-dev uv run alembic upgrade head
```

## Обычный цикл разработки

Если изменился только код в [`services/backend/llm_agent_platform/`](services/backend/llm_agent_platform:1), достаточно:

```bash
docker compose restart backend
```

Если менялся frontend login/admin UI slice или `user_service`, используйте соответствующий restart в `docker-compose-dev.yml` contour.

## Что именно смонтировано

Основные bind-mounts в [`docker-compose.yml`](docker-compose.yml:7):

- [`./services/backend/llm_agent_platform:/app/llm_agent_platform`](docker-compose.yml:9)
- [`./services/backend/pyproject.toml:/app/pyproject.toml`](docker-compose.yml:11)
- [`./services/backend/uv.lock:/app/uv.lock`](docker-compose.yml:12)
- [`./secrets:/app/secrets`](docker-compose.yml:16)

Отдельно также монтируются внешние runtime директории для state и logs.

## Что пока не входит в scope

- автоматический hot reload без restart контейнера
- production deployment scenario

## Current dev auth contour

- `Frontend service` выполняет login against `user_service` по `authApiBaseUrl`.
- `Backend service` использует `JWT_SHARED_SECRET` для проверки admin JWT.
- Public provider routes продолжают жить отдельно от admin JWT boundary.

Для production запусков зарезервирована страница [`docs/run/prod.md`](docs/run/prod.md:1).

FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.28 /uv /uvx /bin/

WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости через uv (жесткая фиксация)
RUN uv sync --frozen --no-dev

# Копируем весь код проекта (игнорируя файлы из .dockerignore)
COPY . .

# Открываем порт
EXPOSE 4000

# Запускаем сервер через package entrypoint
CMD ["uv", "run", "-m", "llm_agent_platform"]

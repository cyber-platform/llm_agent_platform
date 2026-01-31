FROM python:3.11-slim
COPY --from=ghcr.io/astral-sh/uv:0.9.28 /uv /uvx /bin/

WORKDIR /app

# Копируем файлы зависимостей
COPY pyproject.toml uv.lock ./

# Устанавливаем зависимости через uv (жесткая фиксация)
RUN uv sync --frozen --no-dev

# Копируем код
COPY main.py .

# Открываем порт
EXPOSE 4000

# Запускаем сервер через uv run
CMD ["uv", "run", "main.py"]
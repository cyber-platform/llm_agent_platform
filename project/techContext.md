# Технический контекст

## Стек

- Язык: Python 3.13
- Runtime framework: Flask
- HTTP client: `httpx`
- Управление зависимостями: `uv`
- Контейнерный runtime: Docker, Docker Compose

## Runtime-контекст продукта

- Публичный API surface: OpenAI-compatible endpoints
- Текущий архитектурный стиль: provider-centric routing с provider-local catalogs и groups
- В документации проекта используются Google OAuth, Google Service Accounts и provider-specific OAuth flows, включая `openai-chatgpt`

## Внешние зависимости

- Google Cloud Vertex AI API
- Google Cloud Code Assist / Cloud Code related endpoints
- Google OAuth 2.0
- OpenAI ChatGPT/Codex OAuth и backend APIs для provider `openai-chatgpt`

## Environment

- Основная среда разработки: Linux Ubuntu 24.04 LTS
- Layout для secrets и runtime state описан в [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1) и provider-specific документации в [`docs/providers/`](docs/providers:1)

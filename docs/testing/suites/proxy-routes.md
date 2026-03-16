# Suite: Proxy routes smoke and endpoint coverage

## Scope
- Smoke-проверка импорта приложения и регистрации blueprint-маршрутов.
- Endpoint-тест `/v1/models` для базовой проверки контракта списка моделей.
- Тесты native Gemini proxy (`/v1/models/<model>:generateContent`, `/v1/models/<model>:streamGenerateContent`) в quota-контуре.
- Тесты parity relay (`/parity-relay/<path>`) для non-stream и stream проксирования.

## Requirement Traceability
- Requirement: укрепление testability/maintainability после изменения структуры маршрутов.
- Canonical references:
  - Архитектура pipeline: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
  - Карта компонентов: [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
- Script:
  - [`test_refactor_p2_routes.py`](tests/test_refactor_p2_routes.py)

## Verification Command
- `uv run python -m unittest tests/test_refactor_p2_routes.py`
- `uv run python -m unittest discover -s tests -p "test_*.py"`

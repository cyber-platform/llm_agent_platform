# Suite: Proxy routes smoke and endpoint coverage

## Scope
- Smoke-проверка импорта приложения и регистрации blueprint-маршрутов.
- Endpoint-тесты `/<provider_name>/v1/models` и `/<provider_name>/<group_name>/v1/models` для provider-scoped контракта списка моделей.
- Endpoint-тесты `/<provider_name>/v1/chat/completions` и `/<provider_name>/<group_name>/v1/chat/completions`.
- Тесты native Gemini proxy (`/v1/models/<model>:generateContent`, `/v1/models/<model>:streamGenerateContent`) в quota-контуре.
- Тесты parity relay (`/parity-relay/<path>`) для non-stream и stream проксирования.
- Негативные кейсы unknown provider и unknown group внутри provider namespace.

## Requirement Traceability
- Requirement: provider-scoped routing и provider-local groups по [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:23).
- Canonical references:
  - Архитектура pipeline: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
  - Карта компонентов: [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
- Script:
  - [`llm_agent_platform/tests/test_refactor_p2_routes.py`](llm_agent_platform/tests/test_refactor_p2_routes.py:1)

## Verification Command
- `uv run python -m unittest llm_agent_platform/tests/test_refactor_p2_routes.py`
- `uv run python -m unittest discover -s llm_agent_platform/tests -p "test_*.py"`

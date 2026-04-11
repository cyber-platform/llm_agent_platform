# Suite: Proxy routes smoke and endpoint coverage

## Suite ID
- `TS-PROXY-ROUTES`

## Documentation roots
- `docs/testing/test-map.md`
- `docs/testing/traceability.md`
- `docs/testing/suites/proxy-routes.md`

## Implementation roots
- `llm_agent_platform/tests/test_refactor_p2_routes.py`

## Search anchors
- `TS-PROXY-ROUTES`
- `test_refactor_p2_routes.py`
- `/v1/models`
- `/chat/completions`

## Scope
- Smoke-проверка импорта приложения и регистрации blueprint-маршрутов.
- Endpoint-тесты `/<provider_name>/v1/models` и `/<provider_name>/<group_name>/v1/models` для `LLM provider`-scoped контракта списка моделей.
- Endpoint-тесты `/<provider_name>/v1/chat/completions` и `/<provider_name>/<group_name>/v1/chat/completions`.
- Тесты native Gemini proxy (`/v1/models/<model>:generateContent`, `/v1/models/<model>:streamGenerateContent`) в quota-контуре.
- Тесты parity relay (`/parity-relay/<path>`) для non-stream и stream проксирования.
- Негативные кейсы unknown `LLM provider` и unknown group внутри `LLM provider` namespace.

## Requirement Traceability
- Requirement: `LLM provider`-scoped routing и `LLM provider`-local groups по [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:23).
- Rollout metadata:
  - suite anchor: `TS-PROXY-ROUTES`
  - future case anchors: `TC-PROXY-ROUTES-...`
- Canonical references:
  - Архитектура pipeline: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
  - Карта компонентов: [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
- Script:
  - [`llm_agent_platform/tests/test_refactor_p2_routes.py`](llm_agent_platform/tests/test_refactor_p2_routes.py:1)

## Verification Command
- `uv run python -m unittest llm_agent_platform/tests/test_refactor_p2_routes.py`
- `uv run python -m unittest discover -s llm_agent_platform/tests -p "test_*.py"`

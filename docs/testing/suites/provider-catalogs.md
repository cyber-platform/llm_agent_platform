# Suite: Provider-local catalogs

## Scope
- Проверка `bootstrap catalog` для static providers.
- Проверка provider-local model lists без route hardcode.
- Проверка static catalog baseline для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1).

## Requirement Traceability
- Requirement: provider-local catalog strategy по [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:60).
- Canonical references:
  - [`docs/contracts/state/openai-chatgpt-oauth-state.schema.json`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:1)
  - [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1)
  - [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- Script:
  - [`llm_agent_platform/tests/test_provider_catalogs.py`](llm_agent_platform/tests/test_provider_catalogs.py:1)

## Verification Command
- `uv run python -m unittest llm_agent_platform/tests/test_provider_catalogs.py`
- `uv run python -m unittest discover -s llm_agent_platform/tests -p "test_*.py"`

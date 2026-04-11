# Suite: LLM provider-local catalogs

## Suite ID
- `TS-PROVIDER-CATALOGS`

## Documentation roots
- `docs/testing/test-map.md`
- `docs/testing/traceability.md`
- `docs/testing/suites/provider-catalogs.md`

## Implementation roots
- `llm_agent_platform/tests/test_provider_catalogs.py`

## Search anchors
- `TS-PROVIDER-CATALOGS`
- `test_provider_catalogs.py`
- `LLM provider-local catalogs`
- `openai-chatgpt`

## Scope
- Проверка `bootstrap catalog` для static providers.
- Проверка `LLM provider`-local model lists без route hardcode.
- Проверка static catalog baseline для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1).

## Requirement Traceability
- Requirement: `LLM provider`-local catalog strategy по [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:60).
- Rollout metadata:
  - suite anchor: `TS-PROVIDER-CATALOGS`
  - future case anchors: `TC-PROVIDER-CATALOGS-...`
- Canonical references:
  - [`docs/contracts/state/openai-chatgpt-oauth-state.schema.json`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:1)
  - [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- Script:
  - [`llm_agent_platform/tests/test_provider_catalogs.py`](llm_agent_platform/tests/test_provider_catalogs.py:1)

## Verification Command
- `uv run python -m unittest llm_agent_platform/tests/test_provider_catalogs.py`
- `uv run python -m unittest discover -s llm_agent_platform/tests -p "test_*.py"`

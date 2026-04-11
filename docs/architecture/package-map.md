# Package Map

## Назначение

Этот документ связывает logical components и layers с реальными Python packages и key modules.

Он является основной package-level точкой навигации для planning, code reading и impact analysis.

## Runtime package map

| Layer | Component | Primary package or module | Key modules | Notes |
| --- | --- | --- | --- | --- |
| Runtime shell | App bootstrap | [`llm_agent_platform/__main__.py`](llm_agent_platform/__main__.py:1) | app creation, blueprint registration | Flask runtime entrypoint |
| API surface | OpenAI-compatible surface | [`llm_agent_platform/api/openai/`](llm_agent_platform/api/openai:1) | `routes.py`, `pipeline.py`, `types.py`, `transform.py`, `streaming.py`, `response_shaper.py` | Main public provider-scoped API path |
| API surface | Native Gemini surface | [`llm_agent_platform/api/gemini/`](llm_agent_platform/api/gemini:1) | `routes.py` | Provider-native route namespace |
| API surface | Parity relay | [`llm_agent_platform/api/parity/`](llm_agent_platform/api/parity:1) | `routes.py` | Capture-relay and parity tooling surface |
| Provider integration | Provider adapters | [`llm_agent_platform/api/openai/providers/`](llm_agent_platform/api/openai/providers:1) | `base.py`, `gemini_cli.py`, `qwen_code.py`, `google_vertex.py`, `openai_chatgpt.py` | Encapsulates provider transport and runtime auth use |
| Provider integration | Execution strategies | [`llm_agent_platform/api/openai/strategies/`](llm_agent_platform/api/openai/strategies:1) | `base.py`, `registry.py`, `direct.py`, `rotate_on_429_rounding.py` | Encapsulates execution policy over providers |
| Auth | Runtime auth and OAuth refresh | [`llm_agent_platform/auth/`](llm_agent_platform/auth:1) | `credentials.py`, `qwen_oauth.py`, `openai_chatgpt_oauth.py` | Provider-specific auth semantics live here |
| Runtime services | Provider registry and catalogs | [`llm_agent_platform/services/provider_registry.py`](llm_agent_platform/services/provider_registry.py:1) | registry loading, descriptor validation, catalog resolution | Uses declarative data from [`llm_agent_platform/provider_registry/`](llm_agent_platform/provider_registry:1) |
| Runtime services | Quota account router | [`llm_agent_platform/services/account_router.py`](llm_agent_platform/services/account_router.py:1) | account selection, cooldown, exhausted state, group isolation | Cross-provider quota runtime service |
| Runtime services | State path resolution | [`llm_agent_platform/services/runtime_state_paths.py`](llm_agent_platform/services/runtime_state_paths.py:1) | account/group usage paths | Runtime mutable state addressing |
| Runtime services | Credentials path resolution | [`llm_agent_platform/services/credentials_paths.py`](llm_agent_platform/services/credentials_paths.py:1) | credentials locator helpers | Separates secrets paths from runtime state paths |
| Runtime services | Provider usage limits | [`llm_agent_platform/services/provider_usage_limits.py`](llm_agent_platform/services/provider_usage_limits.py:1) | monitoring-only usage snapshot adapters | Current implementation materialized for `openai-chatgpt` |
| Runtime services | Quota transport helpers | [`llm_agent_platform/services/quota_transport.py`](llm_agent_platform/services/quota_transport.py:1) | provider-specific 429 classification helpers | Shared by strategies/providers |
| Infrastructure | HTTP transport primitive | [`llm_agent_platform/services/http_pool.py`](llm_agent_platform/services/http_pool.py:1) | singleton `httpx.Client` | Shared network client |
| Infrastructure | Persisted state writer | [`llm_agent_platform/services/account_state_store.py`](llm_agent_platform/services/account_state_store.py:1) | account state, group snapshot, async writer | In-memory-first runtime persistence boundary |
| Infrastructure | Env configuration | [`llm_agent_platform/config.py`](llm_agent_platform/config.py:1) | runtime env loading | Global runtime configuration boundary |
| Shared core | Common helpers | [`llm_agent_platform/core/`](llm_agent_platform/core:1) | `logging.py`, `models.py`, `utils.py` | Shared utility layer |
| Declarative data | Provider descriptors | [`llm_agent_platform/provider_registry/`](llm_agent_platform/provider_registry:1) | `registry.json`, `providers/*.json` | Declarative provider metadata and bootstrap catalogs |
| Evidence | Runtime tests | [`llm_agent_platform/tests/`](llm_agent_platform/tests:1) | contract, routing, quota, provider tests | Executable architecture evidence |

## Package reading heuristics

### Для новой API functionality

Начинать с:

1. [`llm_agent_platform/api/openai/routes.py`](llm_agent_platform/api/openai/routes.py:1)
2. [`llm_agent_platform/api/openai/pipeline.py`](llm_agent_platform/api/openai/pipeline.py:1)
3. relevant provider adapter или strategy

### Для quota or routing functionality

Начинать с:

1. [`llm_agent_platform/services/account_router.py`](llm_agent_platform/services/account_router.py:1)
2. [`llm_agent_platform/api/openai/strategies/rotate_on_429_rounding.py`](llm_agent_platform/api/openai/strategies/rotate_on_429_rounding.py:1)
3. relevant provider page и tests

### Для provider onboarding or catalog work

Начинать с:

1. [`llm_agent_platform/provider_registry/registry.json`](llm_agent_platform/provider_registry/registry.json:1)
2. [`llm_agent_platform/provider_registry/providers/`](llm_agent_platform/provider_registry/providers:1)
3. [`llm_agent_platform/services/provider_registry.py`](llm_agent_platform/services/provider_registry.py:1)
4. relevant provider adapter in [`llm_agent_platform/api/openai/providers/`](llm_agent_platform/api/openai/providers:1)

### Для auth work

Начинать с:

1. [`llm_agent_platform/auth/`](llm_agent_platform/auth:1)
2. relevant provider adapter
3. [`docs/auth.md`](docs/auth.md:1)

## Related documents

- Layer model: [`docs/architecture/layers.md`](docs/architecture/layers.md:1)
- Logical component map: [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
- Runtime interactions: [`docs/architecture/runtime-flows.md`](docs/architecture/runtime-flows.md:1)

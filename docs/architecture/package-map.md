# Package Map

## Назначение

Этот документ связывает runtime components с реальными Python packages и key modules.

Он является основной package-level точкой навигации для planning, code reading и impact analysis.

## Component-oriented package map

| Component | Primary packages or modules | Key modules | Notes |
| --- | --- | --- | --- |
| Runtime shell | [`services/backend/llm_agent_platform/__main__.py`](services/backend/llm_agent_platform/__main__.py:1) | app creation, blueprint registration | Flask runtime entrypoint |
| API surfaces | [`services/backend/llm_agent_platform/api/openai/`](services/backend/llm_agent_platform/api/openai:1), [`services/backend/llm_agent_platform/api/gemini/`](services/backend/llm_agent_platform/api/gemini:1), [`services/backend/llm_agent_platform/api/parity/`](services/backend/llm_agent_platform/api/parity:1) | `routes.py` in each surface | HTTP entrypoints and boundary adaptation |
| OpenAI pipeline orchestration | [`services/backend/llm_agent_platform/api/openai/pipeline.py`](services/backend/llm_agent_platform/api/openai/pipeline.py:1), [`services/backend/llm_agent_platform/api/openai/types.py`](services/backend/llm_agent_platform/api/openai/types.py:1), [`services/backend/llm_agent_platform/api/openai/transform.py`](services/backend/llm_agent_platform/api/openai/transform.py:1), [`services/backend/llm_agent_platform/api/openai/streaming.py`](services/backend/llm_agent_platform/api/openai/streaming.py:1), [`services/backend/llm_agent_platform/api/openai/response_shaper.py`](services/backend/llm_agent_platform/api/openai/response_shaper.py:1) | request context, streaming, response shaping | Main OpenAI-compatible execution path |
| Provider integrations | [`services/backend/llm_agent_platform/api/openai/providers/`](services/backend/llm_agent_platform/api/openai/providers:1) | `base.py`, `gemini_cli.py`, `qwen_code.py`, `google_vertex.py`, `openai_chatgpt.py` | `provider implementation`, upstream protocol adaptation and normalization |
| Execution strategy layer | [`services/backend/llm_agent_platform/api/openai/strategies/`](services/backend/llm_agent_platform/api/openai/strategies:1) | `base.py`, `registry.py`, `direct.py`, `rotate_on_429_rounding.py` | Execution policy over `provider implementation` |
| Provider registry and catalogs | [`services/backend/llm_agent_platform/services/provider_registry.py`](services/backend/llm_agent_platform/services/provider_registry.py:1), [`services/backend/llm_agent_platform/provider_registry/`](services/backend/llm_agent_platform/provider_registry:1) | registry loading, descriptor validation, catalog resolution | Declarative metadata and bootstrap catalogs for `abstract provider` |
| Quota and account state runtime | [`services/backend/llm_agent_platform/services/account_router.py`](services/backend/llm_agent_platform/services/account_router.py:1), [`services/backend/llm_agent_platform/services/account_state_store.py`](services/backend/llm_agent_platform/services/account_state_store.py:1), [`services/backend/llm_agent_platform/services/runtime_state_paths.py`](services/backend/llm_agent_platform/services/runtime_state_paths.py:1) | account selection, cooldown, exhausted state, async writer | In-memory-first state with persisted snapshots |
| Runtime services | [`services/backend/llm_agent_platform/services/credentials_paths.py`](services/backend/llm_agent_platform/services/credentials_paths.py:1), [`services/backend/llm_agent_platform/services/provider_usage_limits.py`](services/backend/llm_agent_platform/services/provider_usage_limits.py:1), [`services/backend/llm_agent_platform/services/quota_transport.py`](services/backend/llm_agent_platform/services/quota_transport.py:1) | state-path helpers, usage adapters, semantic `429` helpers | Shared runtime ports used across providers and strategies |
| Auth runtime | [`services/backend/llm_agent_platform/auth/`](services/backend/llm_agent_platform/auth:1) | `credentials.py`, `qwen_oauth.py`, `openai_chatgpt_oauth.py` | `LLM provider`-specific auth semantics |
| Shared infrastructure and core | [`services/backend/llm_agent_platform/config.py`](services/backend/llm_agent_platform/config.py:1), [`services/backend/llm_agent_platform/services/http_pool.py`](services/backend/llm_agent_platform/services/http_pool.py:1), [`services/backend/llm_agent_platform/core/`](services/backend/llm_agent_platform/core:1) | env loading, singleton `httpx.Client`, logging, models, utils | Shared base with no upward runtime dependencies |
| Evidence and verification | [`services/backend/llm_agent_platform/tests/`](services/backend/llm_agent_platform/tests:1) | contract, routing, quota, `LLM provider` tests | Executable architecture evidence, not runtime component |

## Package reading heuristics

### Для новой API functionality

Начинать с:

1. [`services/backend/llm_agent_platform/api/openai/routes.py`](services/backend/llm_agent_platform/api/openai/routes.py:1)
2. [`services/backend/llm_agent_platform/api/openai/pipeline.py`](services/backend/llm_agent_platform/api/openai/pipeline.py:1)
3. relevant `provider implementation` или strategy

### Для quota or routing functionality

Начинать с:

1. [`services/backend/llm_agent_platform/services/account_router.py`](services/backend/llm_agent_platform/services/account_router.py:1)
2. [`services/backend/llm_agent_platform/api/openai/strategies/rotate_on_429_rounding.py`](services/backend/llm_agent_platform/api/openai/strategies/rotate_on_429_rounding.py:1)
3. relevant `LLM provider` page и tests

### Для abstract provider onboarding or catalog work

Начинать с:

1. [`services/backend/llm_agent_platform/provider_registry/registry.json`](services/backend/llm_agent_platform/provider_registry/registry.json:1)
2. [`services/backend/llm_agent_platform/provider_registry/providers/`](services/backend/llm_agent_platform/provider_registry/providers:1)
3. [`services/backend/llm_agent_platform/services/provider_registry.py`](services/backend/llm_agent_platform/services/provider_registry.py:1)
4. relevant `provider implementation` in [`services/backend/llm_agent_platform/api/openai/providers/`](services/backend/llm_agent_platform/api/openai/providers:1)

### Для auth work

Начинать с:

1. [`services/backend/llm_agent_platform/auth/`](services/backend/llm_agent_platform/auth:1)
2. relevant `provider implementation`
3. [`docs/auth.md`](docs/auth.md:1)

### Для component-level impact analysis

Начинать с:

1. [`component-view.md`](./component-view.md)
2. [`component-map.md`](./component-map.md)
3. строки этого package map для затронутого component
4. [`traceability-map.md`](./traceability-map.md)

## Related documents

- Layer model: [`docs/architecture/layers.md`](docs/architecture/layers.md:1)
- `C4 Component`: [`docs/architecture/component-view.md`](docs/architecture/component-view.md:1)
- Code-oriented component map: [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
- Runtime interactions: [`docs/architecture/runtime-flows.md`](docs/architecture/runtime-flows.md:1)

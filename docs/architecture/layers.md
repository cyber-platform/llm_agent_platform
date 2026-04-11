# Layers

## Назначение

Этот документ фиксирует layer model для основного runtime container и задаёт правила зависимостей между слоями.

Он не заменяет C4-like zoom navigation, а конкретизирует внутреннюю организацию container-level runtime.

## Layer model

### 1. Runtime shell layer

- Назначение: собрать Flask app, зарегистрировать blueprints, выполнить startup wiring.
- Primary code: [`llm_agent_platform/__main__.py`](llm_agent_platform/__main__.py:1)

### 2. API surface layer

- Назначение: HTTP entrypoints, URL namespace, request/response adaptation на boundary process.
- Primary code:
  - [`llm_agent_platform/api/openai/routes.py`](llm_agent_platform/api/openai/routes.py:1)
  - [`llm_agent_platform/api/gemini/routes.py`](llm_agent_platform/api/gemini/routes.py:1)
  - [`llm_agent_platform/api/parity/routes.py`](llm_agent_platform/api/parity/routes.py:1)

### 3. Application and pipeline layer

- Назначение: orchestration request path, context building, provider selection, strategy selection, response path composition.
- Primary code:
  - [`llm_agent_platform/api/openai/pipeline.py`](llm_agent_platform/api/openai/pipeline.py:1)
  - [`llm_agent_platform/api/openai/types.py`](llm_agent_platform/api/openai/types.py:1)
  - [`llm_agent_platform/api/openai/transform.py`](llm_agent_platform/api/openai/transform.py:1)
  - [`llm_agent_platform/api/openai/streaming.py`](llm_agent_platform/api/openai/streaming.py:1)
  - [`llm_agent_platform/api/openai/response_shaper.py`](llm_agent_platform/api/openai/response_shaper.py:1)

### 4. Provider integration layer

- Назначение: provider-specific transport/auth/runtime adapters и execution policies поверх adapters.
- Primary code:
  - [`llm_agent_platform/api/openai/providers/`](llm_agent_platform/api/openai/providers:1)
  - [`llm_agent_platform/api/openai/strategies/`](llm_agent_platform/api/openai/strategies:1)

### 5. Runtime services layer

- Назначение: provider registry, account routing, runtime state paths, provider monitoring ports, quota transport helpers.
- Primary code:
  - [`llm_agent_platform/services/provider_registry.py`](llm_agent_platform/services/provider_registry.py:1)
  - [`llm_agent_platform/services/account_router.py`](llm_agent_platform/services/account_router.py:1)
  - [`llm_agent_platform/services/provider_usage_limits.py`](llm_agent_platform/services/provider_usage_limits.py:1)
  - [`llm_agent_platform/services/runtime_state_paths.py`](llm_agent_platform/services/runtime_state_paths.py:1)
  - [`llm_agent_platform/services/credentials_paths.py`](llm_agent_platform/services/credentials_paths.py:1)
  - [`llm_agent_platform/services/quota_transport.py`](llm_agent_platform/services/quota_transport.py:1)

### 6. Auth layer

- Назначение: credentials discovery, runtime OAuth refresh, provider-specific auth state handling.
- Primary code:
  - [`llm_agent_platform/auth/credentials.py`](llm_agent_platform/auth/credentials.py:1)
  - [`llm_agent_platform/auth/qwen_oauth.py`](llm_agent_platform/auth/qwen_oauth.py:1)
  - [`llm_agent_platform/auth/openai_chatgpt_oauth.py`](llm_agent_platform/auth/openai_chatgpt_oauth.py:1)

### 7. Infrastructure and shared core layer

- Назначение: env config, shared HTTP client, persisted state primitives, logging and common utility functions.
- Primary code:
  - [`llm_agent_platform/config.py`](llm_agent_platform/config.py:1)
  - [`llm_agent_platform/services/http_pool.py`](llm_agent_platform/services/http_pool.py:1)
  - [`llm_agent_platform/services/account_state_store.py`](llm_agent_platform/services/account_state_store.py:1)
  - [`llm_agent_platform/core/`](llm_agent_platform/core:1)

### 8. SoT and evidence layer

- Назначение: canonical docs, contracts, provider pages, ADRs and tests.
- Primary locations:
  - [`docs/`](docs:1)
  - [`llm_agent_platform/tests/`](llm_agent_platform/tests:1)

Этот слой не является runtime Python layer, но обязателен для change planning и traceability.

## Dependency rules

### Allowed dependency directions

- Runtime shell -> API surface, auth, infrastructure
- API surface -> application and pipeline; provider-native API surfaces also may call runtime services and auth directly when they are not routed through the common pipeline
- Application and pipeline -> provider integration, runtime services, infrastructure, shared core
- Provider integration -> auth, runtime services, infrastructure, shared core
- Runtime services -> auth ports, infrastructure, shared core, declarative registry data
- Auth -> infrastructure, shared core
- Infrastructure and shared core -> no upward dependency on runtime-specific layers

### Practical reading rule

Если новая логика меняет HTTP contract, начинать нужно с API surface и pipeline layers.

Если новая логика меняет provider behavior, начинать нужно с provider integration layer и provider page.

Если новая логика меняет selection, cooldown, quota или state restore, начинать нужно с runtime services layer.

## Layer-to-package navigation

Package realization каждого слоя сведена в [`docs/architecture/package-map.md`](docs/architecture/package-map.md:1).

## Related rationale

- Provider-centric routing: [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1)
- State persistence: [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
- Monitoring/admin boundary: [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)

# Component Map

## Назначение

Этот документ даёт code-oriented карту компонентов платформы.

Он отвечает на вопросы:

- где в коде materialized каждый runtime component;
- в какие Python packages и модули идти для детального code reading;
- какой focused document использовать, если нужен не кодовый, а архитектурный zoom.

Для layer model см. [`layers.md`](./layers.md).

Для `C4 Component` view см. [`component-view.md`](./component-view.md).

Для package-level mapping см. [`package-map.md`](./package-map.md).

## Component-to-code map

| Component | Primary code | Куда идти дальше | Focused architecture docs |
| --- | --- | --- | --- |
| Runtime shell | [`services/backend/llm_agent_platform/__main__.py`](../../services/backend/llm_agent_platform/__main__.py) | app factory, blueprint registration | [`container-view.md`](./container-view.md) |
| API surfaces | [`services/backend/llm_agent_platform/api/openai/`](../../services/backend/llm_agent_platform/api/openai), [`services/backend/llm_agent_platform/api/gemini/`](../../services/backend/llm_agent_platform/api/gemini), [`services/backend/llm_agent_platform/api/parity/`](../../services/backend/llm_agent_platform/api/parity) | `routes.py`, boundary request handling | [`runtime-flows.md`](./runtime-flows.md) |
| OpenAI pipeline orchestration | [`services/backend/llm_agent_platform/api/openai/pipeline.py`](../../services/backend/llm_agent_platform/api/openai/pipeline.py), [`services/backend/llm_agent_platform/api/openai/types.py`](../../services/backend/llm_agent_platform/api/openai/types.py), [`services/backend/llm_agent_platform/api/openai/streaming.py`](../../services/backend/llm_agent_platform/api/openai/streaming.py), [`services/backend/llm_agent_platform/api/openai/response_shaper.py`](../../services/backend/llm_agent_platform/api/openai/response_shaper.py) | context build, stream and non-stream path | [`openai-chat-completions-pipeline.md`](./openai-chat-completions-pipeline.md) |
| Provider integrations | [`services/backend/llm_agent_platform/api/openai/providers/`](../../services/backend/llm_agent_platform/api/openai/providers) | `provider implementation`, upstream protocol adaptation and normalization | [`../providers/index.md`](../providers/index.md) |
| Execution strategy layer | [`services/backend/llm_agent_platform/api/openai/strategies/`](../../services/backend/llm_agent_platform/api/openai/strategies) | direct execution, retries, semantic `429` handling | [`quota-account-rotation-groups-and-models.md`](./quota-account-rotation-groups-and-models.md) |
| Provider registry and catalogs | [`services/backend/llm_agent_platform/services/provider_registry.py`](../../services/backend/llm_agent_platform/services/provider_registry.py), [`services/backend/llm_agent_platform/provider_registry/`](../../services/backend/llm_agent_platform/provider_registry) | `abstract provider` descriptor loading, catalog resolution | [`../providers/index.md`](../providers/index.md) |
| Quota and account state runtime | [`services/backend/llm_agent_platform/services/account_router.py`](../../services/backend/llm_agent_platform/services/account_router.py), [`services/backend/llm_agent_platform/services/account_state_store.py`](../../services/backend/llm_agent_platform/services/account_state_store.py), [`services/backend/llm_agent_platform/services/runtime_state_paths.py`](../../services/backend/llm_agent_platform/services/runtime_state_paths.py) | account pool state, group snapshots, async persistence | [`quota-group-state-snapshot-and-state-dir.md`](./quota-group-state-snapshot-and-state-dir.md) |
| Runtime services | [`services/backend/llm_agent_platform/services/openai_chatgpt_admin_monitoring.py`](../../services/backend/llm_agent_platform/services/openai_chatgpt_admin_monitoring.py), [`services/backend/llm_agent_platform/services/provider_usage_limits.py`](../../services/backend/llm_agent_platform/services/provider_usage_limits.py), [`services/backend/llm_agent_platform/services/credentials_paths.py`](../../services/backend/llm_agent_platform/services/credentials_paths.py), [`services/backend/llm_agent_platform/services/quota_transport.py`](../../services/backend/llm_agent_platform/services/quota_transport.py), [`services/backend/llm_agent_platform/api/admin/routes.py`](../../services/backend/llm_agent_platform/api/admin/routes.py) | monitoring runtime store, admin read-model/materialization, monitoring ports, state path helpers, quota helper ports | [`admin-monitoring-read-model.md`](./admin-monitoring-read-model.md), [`admin-monitoring-refresh-subsystem.md`](./admin-monitoring-refresh-subsystem.md), [`platform-monitoring-runtime.md`](./platform-monitoring-runtime.md) |
| Auth runtime | [`services/backend/llm_agent_platform/auth/`](../../services/backend/llm_agent_platform/auth) | credentials discovery, `LLM provider`-specific OAuth refresh | [`../auth.md`](../auth.md) |
| Shared infrastructure and core | [`services/backend/llm_agent_platform/config.py`](../../services/backend/llm_agent_platform/config.py), [`services/backend/llm_agent_platform/services/http_pool.py`](../../services/backend/llm_agent_platform/services/http_pool.py), [`services/backend/llm_agent_platform/core/`](../../services/backend/llm_agent_platform/core) | env loading, HTTP client, shared helpers | [`layers.md`](./layers.md) |

## Workspace boundaries

В scope этой карты входят:

- runtime package [`services/backend/llm_agent_platform/`](../../services/backend/llm_agent_platform)
- bootstrap scripts [`services/backend/scripts/`](../../services/backend/scripts)
- canonical docs and contracts in [`docs/`](../)

Внешние nested repos не входят в runtime package map и рассматриваются как reference-only context:

- [`qwen-code/`](../../qwen-code)
- [`gemini-cli/`](../../gemini-cli)
- [`kilocode/`](../../kilocode)

## Related documents

- architecture entrypoint: [`index.md`](./index.md)
- `C4 Component`: [`component-view.md`](./component-view.md)
- package-level traceability: [`package-map.md`](./package-map.md)
- runtime scenarios: [`runtime-flows.md`](./runtime-flows.md)

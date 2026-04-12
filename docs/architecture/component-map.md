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
| Runtime shell | [`llm_agent_platform/__main__.py`](../../llm_agent_platform/__main__.py) | app factory, blueprint registration | [`container-view.md`](./container-view.md) |
| API surfaces | [`llm_agent_platform/api/openai/`](../../llm_agent_platform/api/openai), [`llm_agent_platform/api/gemini/`](../../llm_agent_platform/api/gemini), [`llm_agent_platform/api/parity/`](../../llm_agent_platform/api/parity) | `routes.py`, boundary request handling | [`runtime-flows.md`](./runtime-flows.md) |
| OpenAI pipeline orchestration | [`llm_agent_platform/api/openai/pipeline.py`](../../llm_agent_platform/api/openai/pipeline.py), [`llm_agent_platform/api/openai/types.py`](../../llm_agent_platform/api/openai/types.py), [`llm_agent_platform/api/openai/streaming.py`](../../llm_agent_platform/api/openai/streaming.py), [`llm_agent_platform/api/openai/response_shaper.py`](../../llm_agent_platform/api/openai/response_shaper.py) | context build, stream and non-stream path | [`openai-chat-completions-pipeline.md`](./openai-chat-completions-pipeline.md) |
| Provider integrations | [`llm_agent_platform/api/openai/providers/`](../../llm_agent_platform/api/openai/providers) | `provider implementation`, upstream protocol adaptation and normalization | [`../providers/index.md`](../providers/index.md) |
| Execution strategy layer | [`llm_agent_platform/api/openai/strategies/`](../../llm_agent_platform/api/openai/strategies) | direct execution, retries, semantic `429` handling | [`quota-account-rotation-groups-and-models.md`](./quota-account-rotation-groups-and-models.md) |
| Provider registry and catalogs | [`llm_agent_platform/services/provider_registry.py`](../../llm_agent_platform/services/provider_registry.py), [`llm_agent_platform/provider_registry/`](../../llm_agent_platform/provider_registry) | `abstract provider` descriptor loading, catalog resolution | [`../providers/index.md`](../providers/index.md) |
| Quota and account state runtime | [`llm_agent_platform/services/account_router.py`](../../llm_agent_platform/services/account_router.py), [`llm_agent_platform/services/account_state_store.py`](../../llm_agent_platform/services/account_state_store.py), [`llm_agent_platform/services/runtime_state_paths.py`](../../llm_agent_platform/services/runtime_state_paths.py) | account pool state, group snapshots, async persistence | [`quota-group-state-snapshot-and-state-dir.md`](./quota-group-state-snapshot-and-state-dir.md) |
| Runtime services | [`llm_agent_platform/services/openai_chatgpt_admin_monitoring.py`](../../llm_agent_platform/services/openai_chatgpt_admin_monitoring.py), [`llm_agent_platform/services/provider_usage_limits.py`](../../llm_agent_platform/services/provider_usage_limits.py), [`llm_agent_platform/services/credentials_paths.py`](../../llm_agent_platform/services/credentials_paths.py), [`llm_agent_platform/services/quota_transport.py`](../../llm_agent_platform/services/quota_transport.py), [`llm_agent_platform/api/admin/routes.py`](../../llm_agent_platform/api/admin/routes.py) | monitoring runtime store, admin read-model/materialization, monitoring ports, state path helpers, quota helper ports | [`admin-monitoring-read-model.md`](./admin-monitoring-read-model.md), [`admin-monitoring-refresh-subsystem.md`](./admin-monitoring-refresh-subsystem.md), [`platform-monitoring-runtime.md`](./platform-monitoring-runtime.md) |
| Auth runtime | [`llm_agent_platform/auth/`](../../llm_agent_platform/auth) | credentials discovery, `LLM provider`-specific OAuth refresh | [`../auth.md`](../auth.md) |
| Shared infrastructure and core | [`llm_agent_platform/config.py`](../../llm_agent_platform/config.py), [`llm_agent_platform/services/http_pool.py`](../../llm_agent_platform/services/http_pool.py), [`llm_agent_platform/core/`](../../llm_agent_platform/core) | env loading, HTTP client, shared helpers | [`layers.md`](./layers.md) |

## Workspace boundaries

В scope этой карты входят:

- runtime package [`llm_agent_platform/`](../../llm_agent_platform)
- bootstrap scripts [`scripts/`](../../scripts)
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

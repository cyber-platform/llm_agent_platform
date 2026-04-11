# Traceability Map

## Назначение

Этот документ связывает архитектурные capabilities, компоненты, Python packages, contracts, tests и ADR rationale.

Целевая цепочка трассировки:

`capability -> component -> package -> contracts/docs -> tests -> ADR`

## Capability traceability

| Capability | Main components | Main packages | Contracts and docs | Evidence |
| --- | --- | --- | --- | --- |
| Provider-scoped routing | API surface, OpenAI pipeline, provider registry | [`llm_agent_platform/api/openai/`](llm_agent_platform/api/openai:1), [`llm_agent_platform/services/provider_registry.py`](llm_agent_platform/services/provider_registry.py:1) | [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1), [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1) | [`llm_agent_platform/tests/test_refactor_p2_routes.py`](llm_agent_platform/tests/test_refactor_p2_routes.py:1), [`llm_agent_platform/tests/test_openai_contract.py`](llm_agent_platform/tests/test_openai_contract.py:1) |
| Provider-local catalogs | Provider registry, `abstract provider` descriptors | [`llm_agent_platform/services/provider_registry.py`](llm_agent_platform/services/provider_registry.py:1), [`llm_agent_platform/provider_registry/`](llm_agent_platform/provider_registry:1) | [`docs/providers/README.md`](docs/providers/README.md:1), [`docs/contracts/config/provider-descriptor.schema.json`](docs/contracts/config/provider-descriptor.schema.json:1) | [`llm_agent_platform/tests/test_provider_catalogs.py`](llm_agent_platform/tests/test_provider_catalogs.py:1) |
| OpenAI-compatible execution pipeline | API surface, pipeline, `provider implementation`, strategies | [`llm_agent_platform/api/openai/`](llm_agent_platform/api/openai:1), [`llm_agent_platform/api/openai/providers/`](llm_agent_platform/api/openai/providers:1), [`llm_agent_platform/api/openai/strategies/`](llm_agent_platform/api/openai/strategies:1) | [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1) | [`llm_agent_platform/tests/test_openai_contract.py`](llm_agent_platform/tests/test_openai_contract.py:1) |
| Quota account rotation and groups | Account router, quota strategy, `LLM provider` accounts-config | [`llm_agent_platform/services/account_router.py`](llm_agent_platform/services/account_router.py:1), [`llm_agent_platform/api/openai/strategies/rotate_on_429_rounding.py`](llm_agent_platform/api/openai/strategies/rotate_on_429_rounding.py:1) | [`docs/configuration/provider-accounts-config.md`](docs/configuration/provider-accounts-config.md:1), [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1) | [`llm_agent_platform/tests/test_quota_account_router.py`](llm_agent_platform/tests/test_quota_account_router.py:1) |
| Persisted runtime state | Account state store, runtime state paths, account router | [`llm_agent_platform/services/account_state_store.py`](llm_agent_platform/services/account_state_store.py:1), [`llm_agent_platform/services/runtime_state_paths.py`](llm_agent_platform/services/runtime_state_paths.py:1), [`llm_agent_platform/services/account_router.py`](llm_agent_platform/services/account_router.py:1) | [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1), [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1), [`docs/contracts/state/group-quota-state.schema.json`](docs/contracts/state/group-quota-state.schema.json:1) | [`llm_agent_platform/tests/test_quota_account_router.py`](llm_agent_platform/tests/test_quota_account_router.py:1) |
| OpenAI ChatGPT runtime boundary | `openai-chatgpt` provider implementation, OAuth manager, usage adapter | [`llm_agent_platform/api/openai/providers/openai_chatgpt.py`](llm_agent_platform/api/openai/providers/openai_chatgpt.py:1), [`llm_agent_platform/auth/openai_chatgpt_oauth.py`](llm_agent_platform/auth/openai_chatgpt_oauth.py:1), [`llm_agent_platform/services/provider_usage_limits.py`](llm_agent_platform/services/provider_usage_limits.py:1) | [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1), [`docs/contracts/state/openai-chatgpt-oauth-state.schema.json`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:1) | [`llm_agent_platform/tests/test_openai_chatgpt_runtime.py`](llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1) |
| Auth/environment boundary | Auth layer, config layer, bootstrap scripts | [`llm_agent_platform/auth/`](llm_agent_platform/auth:1), [`llm_agent_platform/config.py`](llm_agent_platform/config.py:1), [`scripts/`](scripts:1) | [`docs/auth.md`](docs/auth.md:1), [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1) | manual bootstrap scripts + runtime smoke path |
| Admin monitoring boundary | Monitoring state model, `LLM provider`-specific monitoring contracts | `LLM provider`-specific monitoring state under [`llm_agent_platform/services/`](llm_agent_platform/services:1) | [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1), [`docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md`](docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md:1) | planned suite [`docs/testing/suites/admin-monitoring-read-model.md`](docs/testing/suites/admin-monitoring-read-model.md:1) |

## Change-planning navigation

### Если меняется public API route or request handling

- Start: [`docs/architecture/system-overview.md`](docs/architecture/system-overview.md:1)
- Then: [`docs/architecture/layers.md`](docs/architecture/layers.md:1)
- Then: [`docs/architecture/package-map.md`](docs/architecture/package-map.md:1)
- Then: [`docs/architecture/runtime-flows.md`](docs/architecture/runtime-flows.md:1)

### Если меняется `LLM provider`-specific behavior

- Start: `LLM provider` page in [`docs/providers/`](docs/providers:1)
- Then: [`docs/architecture/package-map.md`](docs/architecture/package-map.md:1)
- Then: relevant contract and test suite from [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

### Если меняется quota or state semantics

- Start: [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)
- Then: [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
- Then: [`docs/architecture/package-map.md`](docs/architecture/package-map.md:1)

## Notes on materialization

- Этот map связывает как fully materialized runtime areas, так и canonized-but-not-fully-materialized architecture boundaries.
- Если capability уже канонизирована в `docs/`, но runtime package еще не materialized полностью, это должно быть видно через `LLM provider` page, architecture note или planned test suite.

# `openai-chatgpt` capability overlay loader и service

## Контекст

Архитектура provider request policy overrides уже канонизирована в `docs/`.

Для реализации нужен backend service layer, который читает provider capability overlay из `services/backend/provider_configuration/openai-chatgpt/models.json` и отдает normalized model capability records поверх существующего `provider_registry`.

## Goal

Материализовать loader/service для capability overlay `openai-chatgpt`, пригодный для admin read path, optional validation и pipeline policy resolution.

## Scope

В scope:

- загрузка `services/backend/provider_configuration/openai-chatgpt/models.json`;
- schema-aware parsing capability overlay;
- merge semantics с существующим `provider_registry` catalog boundary;
- service API для чтения capability record по `model_id`;
- handling отсутствующего model overlay и malformed config.

Не входит в scope:

- admin routes;
- request policy persistence;
- pipeline overwrite behavior;
- UI.

## Canonical references

- [`docs/architecture/provider-request-policy-overrides.md`](../../docs/architecture/provider-request-policy-overrides.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`docs/contracts/config/openai-chatgpt-model-capabilities-registry.schema.json`](../../docs/contracts/config/openai-chatgpt-model-capabilities-registry.schema.json)
- [`docs/examples/openai-chatgpt-model-capabilities-registry.example.json`](../../docs/examples/openai-chatgpt-model-capabilities-registry.example.json)
- [`services/backend/llm_agent_platform/services/provider_registry.py`](../../services/backend/llm_agent_platform/services/provider_registry.py)

## Dependencies

- Опирается на канонизированный SoT в `docs/`.
- Является dependency для admin capability routes и pipeline policy resolution.

## Implementation notes

1. Capability overlay не должен становиться вторым catalog source вместо `provider_registry`.
2. Service должен трактовать overlay как provider-specific knowledge layer поверх catalog baseline.
3. Отсутствие overlay record для модели не должно silently invent-ить capability defaults.
4. Initial immediate scope: `reasoning_effort` для `gpt-5.4*` и `gpt-5.3-codex`.

## Definition of Done

- Backend умеет загрузить и валидно прочитать `openai-chatgpt` capability overlay.
- Service умеет вернуть capability record по `model_id`.
- Overlay semantics не дублируют provider catalog ownership.
- Есть verification notes для valid config и malformed config path.

## Initial status

- Current State: completed.
- Next Step: use the service from admin capability routes and policy-resolution pipeline tasks.
- Blockers: none.

## Execution notes

- Materialized backend service: `services/backend/llm_agent_platform/services/openai_chatgpt_model_capabilities.py`.
- Checked-in provider overlay: `services/backend/provider_configuration/openai-chatgpt/models.json`.
- Verification covers valid overlay reads, missing overlay semantics, and malformed config rejection in `services/backend/llm_agent_platform/tests/test_provider_catalogs.py`.

## What was done

- Added `OPENAI_CHATGPT_MODEL_CAPABILITIES_PATH` to backend config so the overlay path is explicit and overridable via env.
- Implemented `OpenAIChatGPTModelCapabilitiesService` with typed records for parameter capabilities and constraint rules.
- Service behavior is provider-registry-aware: it loads the `openai-chatgpt` catalog through existing `ProviderRegistry`, uses catalog ownership as the source of truth for `model_id`, and rejects overlay records for unknown models.
- Loader semantics are intentionally non-catalog-owning: if the overlay file is absent, the service returns no capability records instead of inventing defaults.
- Validation covers top-level shape (`version`, `provider_id`, `models`), per-model shape (`parameters`, `constraints`, `raw`), boolean `supported`, required `values/default` for supported parameters, duplicate values, and invalid defaults outside the declared values set.
- Materialized initial overlay records for `gpt-5.4`, `gpt-5.4-mini`, and `gpt-5.3-codex` with `reasoning_effort` as the only currently supported parameter family.
- `gpt-5.4` and `gpt-5.4-mini` currently expose reasoning values `none|low|medium|high|xhigh` with default `none`; `gpt-5.3-codex` exposes `low|medium|high|xhigh` with default `medium`.
- The service exposes `get_model_capabilities(model_id)` for point lookups and `list_model_capabilities()` for future admin/read-model use.
- Added `to_admin_payload()` on capability records so later admin routes can reuse the normalized response shape expected by the model-capabilities read contract.
- Added tests covering: bootstrap catalog behavior staying unchanged, successful merged capability read for a catalog model, missing overlay file returning `None`, missing model overlay returning `None`, unknown overlay `model_id` rejection, and malformed parameter default rejection.
- Verification executed successfully with `uv run python -m unittest llm_agent_platform/tests/test_provider_catalogs.py` and `uv run python -m compileall llm_agent_platform` from `services/backend`.

## Handoff notes

- Task 065 can consume `OpenAIChatGPTModelCapabilitiesService` directly for `GET /admin/model-capabilities/openai-chatgpt/models/<model_id>`.
- Task 066 can reuse the same service as the capability lookup source for policy validation and effective-param resolution.
- Constraint records are already parsed and normalized, but no runtime enforcement was added in this task; enforcement belongs to later pipeline work.
- The current admin payload only includes `provider_id`, `model_id`, `display_name`, `parameters`, and optional `drawer.raw_capability_payload`; if task 065 needs `constraints` in the API response, that should be a conscious contract change.

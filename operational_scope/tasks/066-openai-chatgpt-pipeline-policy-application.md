# Pipeline application для `openai-chatgpt` request policies

## Контекст

Платформа канонизировала `pass-through by default` и `policy-driven mutation only`.

Для runtime path нужно materialize-ить pipeline logic, которая при активной policy вычисляет `effective_request_params`, а при отсутствии policy сохраняет pass-through behavior.

## Goal

Добавить в OpenAI pipeline policy resolution path для `openai-chatgpt` без нарушения существующего provider-centric request handling.

## Scope

В scope:

- чтение key policy в request path;
- загрузка capability overlay при active policy path;
- вычисление `effective_request_params`;
- `force` / `default_if_absent` semantics;
- сохранение pass-through semantics при отсутствии policy.

Не входит в scope:

- admin routes;
- UI;
- расширение beyond initial `reasoning_effort` family.

## Canonical references

- [`docs/architecture/provider-request-policy-overrides.md`](../../docs/architecture/provider-request-policy-overrides.md)
- [`docs/architecture/openai-chat-completions-pipeline.md`](../../docs/architecture/openai-chat-completions-pipeline.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`services/backend/llm_agent_platform/api/openai/pipeline.py`](../../services/backend/llm_agent_platform/api/openai/pipeline.py)
- [`services/backend/llm_agent_platform/api/openai/types.py`](../../services/backend/llm_agent_platform/api/openai/types.py)

## Dependencies

- Зависит от capability overlay service.
- Зависит от request policy registry service.
- Является dependency для adapter-side `reasoning_effort` mapping.

## Implementation notes

1. No policy record => no platform-originated param injection.
2. Capability overlay не должен использоваться как hidden default source для каждого запроса.
3. `effective_request_params` должны вычисляться только в active policy path.
4. Validation behavior against capability overlay должна учитывать configurable toggle.

## Definition of Done

- Pipeline умеет различать pass-through и policy-driven modes.
- `force` и `default_if_absent` semantics materialized.
- Existing request flow не ломается при отсутствии policy.
- Есть verification notes для both no-policy и active-policy cases.

## Initial status

- Current State: completed.
- Next Step: use the materialized `effective_request_params` path for adapter-side parameter family integrations such as task 067.
- Blockers: none.

## Execution notes

- Materialized public-route policy context handoff in `services/backend/llm_agent_platform/api/openai/auth_guard.py` by persisting the authorized `openai-chatgpt` platform key record in Flask request context for downstream pipeline resolution.
- Extended `ChatRequestContext` in `services/backend/llm_agent_platform/api/openai/types.py` with `platform_key_id` and `effective_request_params` so pipeline can distinguish pass-through and active-policy request modes without changing provider routing semantics.
- Added `_resolve_openai_chatgpt_effective_request_params(...)` in `services/backend/llm_agent_platform/api/openai/pipeline.py` to load the key-scoped request policy on the runtime path, touch the capability overlay only when a policy record is active, and compute model-scoped effective params for `force` and `default_if_absent` modes.
- Preserved pass-through-by-default behavior by returning empty `effective_request_params` when the API key has no policy record or when the current target model has no override entry.
- Wired `services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py` to consume `ctx.effective_request_params` first for `reasoning_effort`, falling back to raw client payload when no policy-originated effective value exists.
- Added integration coverage in `services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py` for no-policy pass-through, `force` overwrite, and `default_if_absent` semantics on the public `/openai-chatgpt/v1/chat/completions` route.
- Updated `docs/testing/suites/openai-contract.md` and `docs/testing/test-map.md` so the runtime/pipeline policy contour is discoverable from the canonical testing navigation.

## Verification

- `cd services/backend && uv run python -m compileall llm_agent_platform`
- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_runtime.py`
- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_openai_contract.py`

# `openai-chatgpt` adapter integration для `reasoning_effort`

## Контекст

Initial implementation scope ограничен `reasoning_effort`.

После materialization capability overlay, policy registry и pipeline resolution нужно зафиксировать adapter integration, которая преобразует normalized `reasoning_effort` в provider-specific upstream payload для `openai-chatgpt`.

## Goal

Материализовать end-to-end runtime support для `reasoning_effort` в `openai-chatgpt` provider adapter, совместимый с policy-driven overwrite path.

## Scope

В scope:

- чтение normalized `reasoning_effort` из request context / effective params;
- provider-specific payload mapping в `openai_chatgpt` adapter;
- verification для `gpt-5.4*` и `gpt-5.3-codex` initial model families;
- честный runtime failure path, если upstream отвергает param/value.

Не входит в scope:

- `verbosity` и другие parameter families;
- generalized multi-provider override framework beyond current provider;
- UI work.

## Canonical references

- [`docs/architecture/provider-request-policy-overrides.md`](../../docs/architecture/provider-request-policy-overrides.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`docs/contracts/config/openai-chatgpt-model-capabilities-registry.schema.json`](../../docs/contracts/config/openai-chatgpt-model-capabilities-registry.schema.json)
- [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py`](../../services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py)
- [`operational_scope/research/using_gpt-5.4.md`](../research/using_gpt-5.4.md)

## Dependencies

- Зависит от pipeline policy application task.

## Implementation notes

1. Adapter владеет только provider-specific payload mapping, а не policy resolution.
2. Runtime provider error не должен маскироваться synthetic fallback-логикой.
3. Initial focus: `reasoning_effort` only.
4. Для `gpt-5.3-codex` нужно учитывать, что reasoning values отличаются от GPT-5.4 family по текущему канону.

## Definition of Done

- `reasoning_effort` end-to-end доходит от active key policy до upstream adapter payload.
- Pass-through mode не inject-ит reasoning без policy.
- Provider-level rejection path остается честным.
- Есть verification notes для happy path и runtime rejection path.

## Initial status

- Current State: completed.
- Next Step: use the same adapter-side pattern for future parameter families such as `verbosity`, without moving policy resolution into the adapter.
- Blockers: none.

## Execution notes

- Adapter mapping in `services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py` now preserves normalized string values for `reasoning_effort`, maps legacy disable/off aliases to upstream `none`, and stops dropping `none`, `xhigh` or other non-empty values before the upstream contract sees them.
- `gpt-5.4*` requests now emit `reasoning: { effort: "none" }` when policy or client input resolves to `none`, while `gpt-5.3-codex` keeps `xhigh` pass-through for the current capability canon.
- Runtime path keeps honest provider authority: unsupported values are forwarded to upstream instead of being silently stripped, so provider-side rejection remains visible to the caller.
- Added runtime integration coverage in `services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py` for `gpt-5.4` `none`, `gpt-5.3-codex` `xhigh`, and upstream rejection on invalid reasoning values.
- Updated `docs/testing/suites/openai-contract.md` and `docs/testing/test-map.md` so the adapter-side `reasoning_effort` verification path remains discoverable from the canonical testing index.

## Detailed handoff context

- Main code change is localized in `services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py`: `_map_reasoning_effort(...)` no longer whitelists only `low|medium|high`; it now preserves any non-empty normalized string so the adapter does not hide provider-contract drift.
- The adapter now treats `disable`, `disabled` and `off` as compatibility aliases for upstream `none` instead of dropping the field entirely.
- `prepare_upstream(...)` changed from `if reasoning_effort:` to `if reasoning_effort is not None:` so `reasoning_effort="none"` still produces an explicit upstream `reasoning` object for GPT-5.4 family behavior.
- `payload["include"] = ["reasoning.encrypted_content"]` is now emitted only when `reasoning_effort != "none"`; this keeps non-default reasoning behavior unchanged while avoiding unnecessary encrypted reasoning inclusion for `none`.
- No policy-resolution logic was added to the adapter; the adapter still reads `ctx.effective_request_params` first and only performs provider-specific payload shaping after pipeline resolution.
- Test fixture `_capabilities_payload()` in `services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py` was expanded so runtime tests model the current canon for both GPT-5.4 family and `gpt-5.3-codex`.
- Added explicit runtime cases for three contours: pass-through `none` on `gpt-5.4`, pass-through `xhigh` on `gpt-5.3-codex`, and non-masked upstream rejection for unsupported `reasoning_effort="turbo"`.
- Verification was executed after implementation: `uv run python -m compileall llm_agent_platform` and `uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_runtime.py`, both from `services/backend`.

## Verification

- `cd services/backend && uv run python -m compileall llm_agent_platform`
- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_runtime.py`

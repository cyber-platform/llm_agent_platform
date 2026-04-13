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

- Current State: planned.
- Next Step: materialize adapter-side `reasoning_effort` integration after pipeline merge path.
- Blockers: none.

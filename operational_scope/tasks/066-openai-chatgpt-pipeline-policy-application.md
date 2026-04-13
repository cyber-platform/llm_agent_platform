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

- Current State: planned.
- Next Step: materialize policy resolution in pipeline and add tests.
- Blockers: none.

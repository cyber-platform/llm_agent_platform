# Сравнение provider monitoring semantics для `openai-chatgpt`, `gemini-cli`, `qwen_code`

## Контекст

Platform-wide monitoring runtime нельзя safely обобщить без сравнения реальных monitoring semantics у materialized и ближайших candidate providers.

Сейчас implementation scope intentionally ограничен `openai-chatgpt`, но следующее архитектурное решение должно учитывать различия между polling-based monitoring и request-derived observability.

## Goal

Сравнить monitoring semantics и integration constraints для `openai-chatgpt`, `gemini-cli` и `qwen_code` как input для следующего этапа platform generalization.

## Scope

В scope:

- сравнение upstream monitoring sources;
- сравнение refreshability и request-derived observability;
- сравнение возможных normalized runtime projections;
- фиксация capability matrix и архитектурных ограничений.

Не входит в scope:

- implementation любых provider integrations beyond `openai-chatgpt`;
- final universal contract freeze;
- distributed runtime design.

## Canonical references

- [`operational_scope/tasks/049-platform-monitoring-runtime-sot-and-memory-first-read-model.md`](./049-platform-monitoring-runtime-sot-and-memory-first-read-model.md)
- [`operational_scope/tasks/050-generalized-monitoring-dimensions-contract-design.md`](./050-generalized-monitoring-dimensions-contract-design.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`docs/providers/index.md`](../../docs/providers/index.md)

## Dependencies

- Следует после фиксации platform-wide runtime direction; может потребовать отдельное research pass.

## Implementation notes

1. Нужно явно отделить providers с polling-based monitoring от providers с only request-derived observability.
2. Comparison должен дать input для capability matrix, а не только narrative description.
3. Если documentation gaps окажутся слишком большими, потребуется отдельный research task вместо unsafe assumptions.

## Definition of Done

- Подготовлено сравнение `openai-chatgpt`, `gemini-cli`, `qwen_code` по monitoring semantics.
- Зафиксированы capability differences и architectural implications.
- Сформирован input для generalized `monitoring_dimensions[]` design и future provider onboarding.

## Initial status

- Current State: planned after PoC.
- Next Step: выполнить targeted comparison после завершения immediate `openai-chatgpt` monitoring runtime alignment.
- Blockers: none.

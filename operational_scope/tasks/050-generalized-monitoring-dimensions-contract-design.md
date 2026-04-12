# Generalized `monitoring_dimensions[]` contract design

## Контекст

Для `openai-chatgpt` уже materialized provider-specific monitoring page projection с short/long windows. Однако platform-wide monitoring runtime не должен silently зафиксировать этот shape как universal contract для всех providers, потому что часть providers имеет только request-derived observability.

## Goal

Спроектировать generalized `monitoring_dimensions[]` contract как future-ready platform abstraction для providers с различной monitoring semantics.

## Scope

В scope:

- анализ требований к generalized monitoring contract;
- proposal для `monitoring_dimensions[]` envelope и capability-driven projection model;
- описание границы между common envelope и provider-specific derived fields.

Не входит в scope:

- production implementation;
- retrofit всех существующих providers;
- замена текущей `openai-chatgpt` provider-specific page projection в границе текущего PoC.

## Canonical references

- [`operational_scope/tasks/049-platform-monitoring-runtime-sot-and-memory-first-read-model.md`](./049-platform-monitoring-runtime-sot-and-memory-first-read-model.md)
- [`operational_scope/discussion/2026-04-12-platform-monitoring-runtime-open-questions.md`](../discussion/2026-04-12-platform-monitoring-runtime-open-questions.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)

## Dependencies

- Следует после фиксации platform-wide monitoring runtime SoT.

## Implementation notes

1. Contract должен подходить и для polling-based monitoring, и для request-derived observability.
2. `openai-chatgpt` short/long windows нельзя молча объявлять universal baseline.
3. Нужно сохранить возможность provider-specific page projections поверх common runtime abstraction.

## Definition of Done

- Подготовлен proposal generalized `monitoring_dimensions[]` contract.
- Явно разведены common platform semantics и provider-specific derived views.
- Зафиксированы ограничения и migration path от текущего `openai-chatgpt`-specific projection.

## Initial status

- Current State: planned after PoC.
- Next Step: вернуться после фиксации platform-wide monitoring runtime SoT и completion current PoC slice.
- Blockers: none.

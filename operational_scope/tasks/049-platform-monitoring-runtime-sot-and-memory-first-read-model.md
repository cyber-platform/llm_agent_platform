# Platform-wide monitoring runtime SoT и memory-first read-model

## Контекст

После materialization admin monitoring для `openai-chatgpt` стало видно semantic gap между каноном и runtime path: persisted monitoring artifacts все еще частично участвуют в request-time materialization, хотя архитектурное направление уже смещено к memory-first read-model.

Нужно зафиксировать platform-wide SoT document, который определит общую runtime abstraction для monitoring state, refresh lifecycle и startup hydration без premature universal normalization для всех providers.

## Goal

Зафиксировать SoT для platform-wide monitoring runtime abstraction, где backend читает monitoring state из памяти процесса, а persisted artifacts служат только для restore/audit.

## Scope

В scope:

- новый архитектурный SoT doc для platform-wide monitoring runtime abstraction;
- фиксация memory-first read-model semantics;
- фиксация startup hydration и persistence boundary;
- фиксация provider capability matrix как extension seam;
- ограничение текущей materialization только `openai-chatgpt` provider-specific page projection.

Не входит в scope:

- universal `monitoring_dimensions[]` contract;
- multi-instance coordination;
- materialization для `gemini-cli` и `qwen_code`;
- distributed refresh orchestration.

## Canonical references

- [`docs/architecture/admin-monitoring-read-model.md`](../../docs/architecture/admin-monitoring-read-model.md)
- [`docs/architecture/admin-monitoring-refresh-subsystem.md`](../../docs/architecture/admin-monitoring-refresh-subsystem.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`docs/architecture/drift-register.md`](../../docs/architecture/drift-register.md)
- [`operational_scope/discussion/2026-04-12-platform-monitoring-runtime-open-questions.md`](../discussion/2026-04-12-platform-monitoring-runtime-open-questions.md)

## Dependencies

- Опирается на completed task `048` как на baseline live refresh subsystem для `openai-chatgpt`.

## Implementation notes

1. SoT должен зафиксировать process-local monitoring runtime store как primary runtime delivery source.
2. Persisted files должны быть описаны как restore/audit layer, а не live request source.
3. Startup hydration должен быть отдельным lifecycle step.
4. Provider adapters должны обновлять memory state first, а persisted artifacts second.
5. Admin monitoring page должна читаться только из runtime abstraction.
6. В документе нужно явно отметить, что текущая implementation materialized только для `openai-chatgpt`.

## Definition of Done

- Добавлен SoT document для platform-wide monitoring runtime abstraction.
- В документе явно зафиксированы memory-first semantics, hydration boundary и persistence role.
- Зафиксировано, что generalized normalization еще не freeze-ится.
- Зафиксировано, что multi-instance backend остается open question вне scope текущего PoC.

## Execution summary

- Добавлен новый SoT document [`docs/architecture/platform-monitoring-runtime.md`](../../docs/architecture/platform-monitoring-runtime.md), который фиксирует platform-wide monitoring runtime abstraction.
- В новом документе закреплены:
  - process-local monitoring runtime store как primary runtime Source of Truth;
  - canonical live read path `process-local monitoring runtime store -> backend admin read-model -> frontend UI`;
  - startup hydration как отдельный lifecycle step;
  - persistence boundary, где persisted artifacts используются только для startup hydration, restore after restart и audit/debug trail;
  - memory-first mutation order `memory first -> persistence second`;
  - provider capability matrix как extension seam без premature universal normalization.
- Синхронизирован [`docs/architecture/admin-monitoring-read-model.md`](../../docs/architecture/admin-monitoring-read-model.md): read-model теперь явно описан как чтение только из process-local runtime state, без request-time materialization из persisted artifacts.
- Синхронизирован [`docs/architecture/admin-monitoring-refresh-subsystem.md`](../../docs/architecture/admin-monitoring-refresh-subsystem.md): refresh subsystem теперь явно связан с process-local monitoring runtime, startup hydration boundary и правилом `memory first, persistence second`.
- Синхронизирован provider-specific канон [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md): `openai-chatgpt` зафиксирован как первый materialized provider-specific slice общей platform monitoring runtime abstraction.
- Обновлены навигационные и drift references:
  - [`docs/architecture/index.md`](../../docs/architecture/index.md)
  - [`docs/architecture/drift-register.md`](../../docs/architecture/drift-register.md)
- В drift register semantic gap перенесен из модели `persisted files may still be read live` в explicit open question про multi-instance coordination и future provider normalization.

## Files changed

- [`docs/architecture/platform-monitoring-runtime.md`](../../docs/architecture/platform-monitoring-runtime.md)
- [`docs/architecture/admin-monitoring-read-model.md`](../../docs/architecture/admin-monitoring-read-model.md)
- [`docs/architecture/admin-monitoring-refresh-subsystem.md`](../../docs/architecture/admin-monitoring-refresh-subsystem.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`docs/architecture/index.md`](../../docs/architecture/index.md)
- [`docs/architecture/drift-register.md`](../../docs/architecture/drift-register.md)
- [`operational_scope/tasks_map.md`](../tasks_map.md)

## Follow-up context for next agent

- Этот task закрывает только SoT/documentation layer для platform-wide monitoring runtime.
- Concrete materialization зафиксирована только для `openai-chatgpt`; другие providers не должны автоматически наследовать page shape или refresh semantics этого provider.
- Universal `monitoring_dimensions[]` contract сознательно не freeze-ился и вынесен в отдельную follow-up задачу `050`.
- Multi-instance backend coordination, distributed refresh ownership и durable refresh job history остаются explicit out-of-scope questions; при выходе за single-instance PoC нужен отдельный архитектурный цикл.
- `task-map` синхронизирован: задача `049` помечена как `выполнена`.

## Initial status

- Current State: completed.
- Next Step: использовать platform-wide monitoring runtime SoT как baseline для последующих provider capability decisions и multi-provider monitoring design.
- Blockers: none.

# Materialize memory-first monitoring runtime alignment для `openai-chatgpt`

## Контекст

Задача `049` завершила SoT/documentation слой и зафиксировала platform-wide monitoring runtime abstraction с canonical live read path:

`process-local monitoring runtime store -> backend admin read-model -> frontend UI`.

Текущая runtime materialization для `openai-chatgpt` еще не полностью выровнена с этим каноном: backend monitoring path все еще частично читает persisted monitoring artifacts на request path и сохраняет legacy-compatible file-backed behavior.

Эта задача предназначена для агента-разработчика и должна materialize-ить concrete runtime alignment только для `openai-chatgpt` в границе текущего PoC.

## Goal

Перевести `openai-chatgpt` monitoring runtime на memory-first read-model, где admin monitoring page и refresh subsystem читают только process-local runtime state, а persisted artifacts используются только для startup hydration и durability trail.

## Scope

В scope:

- process-local monitoring runtime store для `openai-chatgpt`;
- startup hydration canonical monitoring state из persisted artifacts;
- memory-first mutation path для background/manual refresh;
- admin read-model чтение только из runtime store;
- persistence как secondary step после memory update;
- удаление request-time зависимости admin monitoring path от legacy file fallback semantics;
- backend tests и test/doc sync для нового runtime behavior.

Не входит в scope:

- materialization для `gemini-cli` и `qwen_code`;
- generalized `monitoring_dimensions[]` contract;
- multi-instance coordination;
- distributed refresh ownership;
- redesign provider capability matrix beyond already accepted SoT.

## Canonical references

- [`docs/architecture/platform-monitoring-runtime.md`](../../docs/architecture/platform-monitoring-runtime.md)
- [`docs/architecture/admin-monitoring-read-model.md`](../../docs/architecture/admin-monitoring-read-model.md)
- [`docs/architecture/admin-monitoring-refresh-subsystem.md`](../../docs/architecture/admin-monitoring-refresh-subsystem.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`operational_scope/tasks/048-admin-monitoring-live-refresh-subsystem-materialization.md`](./048-admin-monitoring-live-refresh-subsystem-materialization.md)
- [`operational_scope/tasks/049-platform-monitoring-runtime-sot-and-memory-first-read-model.md`](./049-platform-monitoring-runtime-sot-and-memory-first-read-model.md)
- [`operational_scope/discussion/2026-04-12-platform-monitoring-runtime-open-questions.md`](../discussion/2026-04-12-platform-monitoring-runtime-open-questions.md)
- [`docs/testing/test-map.md`](../../docs/testing/test-map.md)

## Dependencies

- Опирается на completed task `048` как baseline refresh subsystem implementation.
- Опирается на completed task `049` как архитектурный SoT для memory-first monitoring runtime.
- Не должен автоматически распространять `openai-chatgpt` page shape на другие providers.

## Implementation notes

1. Нужно ввести explicit process-local runtime store для `openai-chatgpt` monitoring state.
2. Startup hydration должен выполняться один раз как отдельный lifecycle step, а не как request-time fallback.
3. `get_provider_page()` и related admin read-model methods должны читать только memory state.
4. Background/manual refresh должны обновлять monitoring state по правилу `memory first -> persistence second`.
5. Persisted `usage_windows.json` и `request_usage.json` остаются durability layer, но не live request source.
6. Legacy `limits.json` не должен оставаться частью admin monitoring read path.
7. Если persistence временно отстает или не удалась, live admin page все равно должна отражать memory truth текущего process.
8. В тестах нужно явно покрыть разрыв между live runtime state и persisted artifact freshness.

## Proposed testing slice

- подтвердить, что admin monitoring page читает runtime state без request-time reread persisted files;
- подтвердить startup hydration initial state из persisted artifacts;
- подтвердить, что refresh сначала меняет live page-visible state, а persistence остается secondary;
- подтвердить отсутствие legacy `limits.json` dependency в admin monitoring path;
- обновить релевантные suites и `docs/testing/test-map.md`, если coverage map меняется.

## Definition of Done

- `openai-chatgpt` monitoring runtime использует explicit memory-first store.
- Admin monitoring read-model больше не зависит от request-time file reads.
- Startup hydration materialized как отдельный lifecycle step.
- Refresh subsystem следует canonical mutation order `memory first -> persistence second`.
- Legacy file-backed behavior убран из live admin read path.
- Automated tests покрывают runtime alignment и не регрессируют existing admin monitoring behavior.

## Initial status

- Current State: completed.
- Next Step: none.
- Blockers: none.

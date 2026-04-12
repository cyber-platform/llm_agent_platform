# Platform monitoring runtime

## Назначение

Этот документ фиксирует platform-wide Source of Truth для monitoring runtime abstraction.

Он задает общие правила для:

- process-local monitoring runtime store;
- startup hydration из persisted artifacts;
- memory-first read path для admin monitoring;
- refresh lifecycle и persistence boundary;
- provider capability matrix как extension seam.

Документ не freeze-ит premature universal normalization для всех providers и не заменяет provider-specific monitoring semantics.

## Problem frame

После materialization admin monitoring и live refresh для `openai-chatgpt` стало видно, что persisted monitoring artifacts еще можно ошибочно трактовать как request-time input layer.

Для текущего архитектурного направления это неверно.

Канонический runtime path должен быть таким:

```text
startup hydration from persisted artifacts -> process-local monitoring runtime store -> backend admin read-model -> frontend UI
```

Persisted artifacts нужны только для restore after restart и audit trail.

## Core principles

1. Monitoring runtime store внутри backend process является primary runtime Source of Truth для monitoring state.
2. Backend admin API читает monitoring state только из process-local runtime abstraction.
3. Persisted monitoring artifacts не участвуют в live request-time materialization.
4. Startup hydration является отдельным lifecycle step до normal runtime serving, а не fallback path на каждый read.
5. Provider adapters сначала обновляют in-memory monitoring state, затем enqueue-ят persisted writes.
6. Provider-specific page projections допускаются, даже если universal normalized monitoring contract еще не зафиксирован.

## Runtime abstraction

Platform-level abstraction должна уметь держать минимум три semantic слоя:

- `routing truth` — runtime availability и block semantics account/group selection;
- `monitoring state` — provider-specific usage windows, freshness metadata и related operator-facing status;
- `refresh runtime state` — active/completed refresh runs, progress и last refresh outcome.

Эти слои могут иметь разные owners, но для admin delivery path они читаются из одной process-local runtime boundary.

## Read-model semantics

Admin monitoring page не должна materialize-иться прямым чтением persisted files.

Канонический live read path:

```text
process-local monitoring runtime store -> backend admin read-model -> frontend UI
```

Следствия:

- async flush lag не должен менять operator-visible live state внутри текущего process;
- page reload и polling не должны re-read persisted monitoring artifacts как substitute for memory;
- provider-specific drawers и tables строятся из runtime abstraction, а не из file layout.

## Startup hydration boundary

Hydration допускается только как startup или explicit restore step.

Canonical lifecycle:

1. backend process discovers configured providers;
2. persisted artifacts, если они есть, читаются в provider-owned hydration step;
3. runtime store получает initial monitoring state;
4. backend начинает normal admin/API serving;
5. background/manual refresh уже работают только через runtime store with memory-first mutations.

Hydration не означает, что persisted artifacts становятся live source после старта.

## Persistence boundary

Persisted monitoring artifacts остаются secondary layer с двумя ролями:

- restore after restart;
- audit/debug trail.

Canonical write order:

```text
provider adapter / refresh subsystem -> mutate in-memory runtime state -> enqueue persisted write
```

Допустимо, что persisted artifact временно отстает от process memory.

Это не считается drift, пока:

- admin read-model читает memory state first;
- routing decisions не зависят от свежести flush на диск;
- restart hydration корректно переносит последний успешно сохраненный snapshot.

## Provider capability matrix

Platform-wide runtime abstraction не должна предполагать одинаковый monitoring contract для всех providers.

Вместо этого канонизируется capability matrix как extension seam.

На текущем этапе важны следующие capability axes:

- provider имеет или не имеет refreshable monitoring API;
- provider имеет polling-based usage windows или только request-derived observability;
- provider materializes dedicated admin page projection или только minimal provider presence;
- provider поддерживает manual refresh action или только background/no refresh semantics.

Эта матрица нужна для runtime branching и page projection design, но не freeze-ит universal `monitoring_dimensions[]` contract.

## Current materialization boundary

Platform-wide abstraction принимается как общий SoT, но текущая concrete materialization ограничена первым provider-specific slice:

- provider-specific monitoring page materialized только для `openai-chatgpt`;
- refresh subsystem materialized только для `openai-chatgpt` monitoring usage state;
- `gemini-cli` и `qwen_code` не обязаны подгоняться под `openai-chatgpt` page shape;
- generalized provider-normalized monitoring surface остается отдельной будущей задачей.

## Out of scope

Этот документ сознательно не freeze-ит:

- multi-instance coordination и distributed refresh ownership;
- durable distributed job history;
- cancel semantics для refresh runs;
- universal `monitoring_dimensions[]` payload;
- обязательную одинаковую page schema для всех providers.

При переходе к multi-instance backend architecture этот SoT должен быть пересмотрен отдельно.

## Revision triggers

Документ нужно пересмотреть при одном из условий:

- backend перестает быть single-instance process-local runtime;
- второй или третий provider получает materialized monitoring page и refresh runtime;
- появляется необходимость durable refresh job history;
- admin surface выходит за local single-user PoC boundary.

## Related documents

- [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)
- [`docs/architecture/admin-monitoring-refresh-subsystem.md`](docs/architecture/admin-monitoring-refresh-subsystem.md:1)
- [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
- [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- [`operational_scope/discussion/2026-04-12-platform-monitoring-runtime-open-questions.md`](operational_scope/discussion/2026-04-12-platform-monitoring-runtime-open-questions.md:1)

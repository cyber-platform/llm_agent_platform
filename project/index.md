# Project Context Index

## Назначение

Этот файл — durable entry point в project-level context для `llm_agent_platform`.

Он нужен, чтобы человек и агент быстро понимали:
- где лежат repository boundaries;
- где зафиксирован technical baseline;
- в каком порядке читать контекст проекта;
- какой слой является engineering SoT, а какой — execution context.

## Порядок чтения

1. `project/gitContext.md` для repository ownership, nested repositories и git boundaries.
2. `project/techContext.md` для technical baseline и environment assumptions.
3. `project/entry-points.md` для concrete loading order и ownership split между слоями контекста.
4. `project/codeStyle.md` для coding style и authoring conventions.

## Границы контекста

- `docs/` — engineering Source of Truth для архитектуры, contracts, provider behavior и testing documentation.
- `project/` — durable repository context, а не архитектурный канон.
- `tasks_descriptions/` — текущий execution layer проекта; по смыслу это transitional equivalent будущего `operational_scope/`.
- `.kilo/` — project-specific Kilo runtime/config layer.

## Current migration note

- Root project пока отстает от более нового layered canon, который уже materialized в `sot_layers/hyper-graph/`.
- На текущем этапе у root проекта еще нет `docs/index.md` и `operational_scope/`.
- Пока migration не завершена, navigation идет через `AGENTS.md`, `project/`, канонические entry points в `docs/` и `tasks_descriptions/tasks_map.md`.

## Связанные файлы

- `AGENTS.md`
- `project/gitContext.md`
- `project/techContext.md`
- `project/entry-points.md`
- `project/codeStyle.md`
- `tasks_descriptions/tasks_map.md`

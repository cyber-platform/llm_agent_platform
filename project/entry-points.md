# Entry Points

## Назначение

Этот файл фиксирует concrete project-local реализацию context-entry model для root проекта `llm_agent_platform`.

Его задача - показать:
- какие entry-point artifacts используются в текущем root layout;
- в каком порядке человек и агент должны читать контекст;
- какой слой чем владеет;
- как работает переключение в autonomous nested project.

## Порядок чтения контекста

Для root проекта используется такой baseline route:

1. `AGENTS.md` как top-level router artifact.
2. `project/index.md` как durable context entry.
3. `project/gitContext.md` для repository ownership, nested repositories и git boundaries.
4. `project/techContext.md` для technical baseline и environment assumptions.
5. `project/codeStyle.md` для coding style и authoring conventions.
6. Канонические engineering docs из `AGENTS.md`:
   - `docs/vision.md`
   - `docs/architecture/component-map.md`
   - `docs/architecture/openai-chat-completions-pipeline.md`
   - `docs/providers/index.md`
   - `docs/providers/openai-chatgpt.md`
   - `docs/contracts/`
   - `docs/testing/test-map.md`
7. `operational_scope/tasks_map.md` только когда нужен execution context текущей итерации.
8. `.kilo/` artifacts только когда нужен Kilo-specific behavior или runtime/config layer.

Если temporary execution artifact конфликтует с `docs/`, следуй `docs/`.

## Ownership model

### `AGENTS.md`

`AGENTS.md` владеет только:
- кратким описанием проекта;
- repository-wide loading order;
- links на основные entry points;
- правилом переключения в local context autonomous nested project.

`AGENTS.md` не владеет:
- подробными git boundaries;
- полным technical baseline;
- code style;
- architecture canon.

### `project/`

`project/` владеет durable project context:
- repository boundaries;
- technical baseline;
- loading-order detail;
- code style;
- migration notes о текущем state root layout.

`project/` не является engineering SoT.

### `docs/`

`docs/` владеет:
- архитектурой;
- provider behavior;
- contracts;
- testing documentation;
- другими long-lived engineering decisions.

### `operational_scope/`

`operational_scope/` владеет временным execution context:
- tasks;
- plans;
- research;
- ideas;
- feedback.

Этот слой не должен подменять `docs/`.

По смыслу это transitional equivalent будущего `operational_scope/`.

### `.kilo/`

`.kilo/` владеет Kilo-specific project layer:
- rules;
- agents;
- commands;
- other target-specific config artifacts.

## Nested repo context switching

В root проекте нужно поддерживать autonomous nested projects, перечисленные в `project/gitContext.md`.

Текущее baseline rule:
- если task scope уходит в autonomous nested project со своим `AGENTS.md`, нужно переключиться на его local context;
- parent root project используется только как outer navigation, пока task scope не вошел в nested project;
- parent root не должен навязывать nested project свой `project/`, `docs/`, execution layer или `.kilo/` canon;
- fallback inheritance допустим только для отсутствующего слоя.

На текущем этапе это особенно важно для `sot_layers/hyper-graph/`, который уже живет по более новому layered canon.

## Current root gaps

- У root проекта пока нет `docs/index.md`.
- Execution layer root проекта теперь materialized как `operational_scope/`.
- Поэтому route выше честно отражает current reality, а не future target state.

## Связанные файлы

- `AGENTS.md`
- `project/index.md`
- `project/gitContext.md`
- `project/techContext.md`
- `project/codeStyle.md`
- `docs/vision.md`
- `docs/providers/index.md`
- `docs/testing/test-map.md`
- `operational_scope/tasks_map.md`

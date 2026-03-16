# Task: Перенести реализованные планы из `plans/` в архитектурную документацию проекта (Architect stage)

## Контекст

В репозитории накопились проектные планы в [`plans/`](plans/015-016-account-rotation-architecture.md:1), часть из которых уже реализована или зафиксирована как принятая архитектура.

Нужно выполнить «упаковку» в каноническую архитектурную документацию проекта по правилам Architect stage:
- обновить `docs/architecture/*` (component-map / boundaries / flows),
- при необходимости зафиксировать решения через ADR в `docs/adr/*`,
- поддержать DRY: `plans/` остаются как рабочие черновики/спеки, но канон должен быть в `docs/`.

## Architecture Context References
- [x] Правила документации: [`documentation.md`](.kilocode/rules/documentation.md:1)
- [x] Memory Bank patterns: [`systemPatterns.md`](.kilocode/rules/memory-bank/systemPatterns.md:1)
- [x] Текущая карта компонентов: [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)

## Specification References
- [x] Планы-кандидаты (инвентаризация обязательна):
  - [`plans/018-refactor-p1-architecture.md`](plans/018-refactor-p1-architecture.md:1)
  - [`plans/018-refactor-p1-domain-model.md`](plans/018-refactor-p1-domain-model.md:1)
  - [`plans/015-016-account-rotation-architecture.md`](plans/015-016-account-rotation-architecture.md:1)
  - [`plans/019-env-separation-runtime-vs-oauth-bootstrap-spec.md`](plans/019-env-separation-runtime-vs-oauth-bootstrap-spec.md:1)
  - [`plans/020-repo-layout-src-model_proxy-and-scripts-spec.md`](plans/020-repo-layout-src-model_proxy-and-scripts-spec.md:1)

## Инвентаризация планов (plan -> tasks -> verification -> canonical docs/ADR -> status)

| Plan | Related tasks | Verification evidence | Canonical docs/ADR (SoT) | Status | Notes |
|---|---|---|---|---|---|
| [`plans/015-016-account-rotation-architecture.md`](plans/015-016-account-rotation-architecture.md:1) | [`tasks_descriptions/tasks/021-rotation-policies-groups-and-models.md`](tasks_descriptions/tasks/021-rotation-policies-groups-and-models.md:1), [`tasks_descriptions/tasks/022-test-design-rotation-policies-groups-and-models.md`](tasks_descriptions/tasks/022-test-design-rotation-policies-groups-and-models.md:1) | `uv run python -m compileall api auth core services main.py tests` (ok) + `uv run python -m unittest discover -s tests -p "test_*.py"` (`Ran 31 tests`, `OK`) | Pending: new `docs/architecture/*` page + ADR-0017 | implemented | Реализация и тесты уже есть, но канон в `docs/architecture/` и ADR про decision URL-prefix ещё не оформлены |
| [`plans/018-refactor-p1-architecture.md`](plans/018-refactor-p1-architecture.md:1) + [`plans/018-refactor-p1-domain-model.md`](plans/018-refactor-p1-domain-model.md:1) | [`tasks_descriptions/tasks/018-refactor.md`](tasks_descriptions/tasks/018-refactor.md:1) | `uv run python -m compileall ...` (ok) + `uv run python -m unittest discover ...` (ok) | Pending: new `docs/architecture/*` page | implemented | Рефактор уже реализован (Providers/Strategies/Pipeline), канон нужно «упаковать» в `docs/architecture/` |
| [`plans/019-env-separation-runtime-vs-oauth-bootstrap-spec.md`](plans/019-env-separation-runtime-vs-oauth-bootstrap-spec.md:1) | (task to be created/linked) | Нет L1-L3 автотестов (suite [`docs/testing/suites/config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md:1) помечен `planned`) | [`docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1), [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1) | accepted-but-not-implemented | Решение принято и задокументировано, но тестовый/verification контур и полнота внедрения требуют отдельной задачи |
| [`plans/020-repo-layout-src-model_proxy-and-scripts-spec.md`](plans/020-repo-layout-src-model_proxy-and-scripts-spec.md:1) | (task to be created/linked) | Не верифицируется: `src/` layout в репозитории отсутствует | [`docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md`](docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md:1) | draft (ADR proposed) | ADR-0016 имеет статус Proposed, реализация не выполнена |

## Test Design References
- [x] Индекс тестов: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Workflow References
- [x] none

## Цель

- Сделать архитектурную документацию в `docs/` каноническим источником истины по уже реализованным решениям.
- Снизить зависимость от `plans/` как единственного носителя архитектуры.

## Шаги реализации

- [ ] Инвентаризировать `plans/` и для каждого плана определить статус: implemented / accepted-but-not-implemented / draft.
- [ ] Для планов со статусом implemented:
  - [ ] перенести ключевые решения в `docs/architecture/*` (или создать новый документ),
  - [ ] при наличии decision triggers — оформить ADR в `docs/adr/*`.
- [ ] Для планов accepted-but-not-implemented:
  - [ ] оставить как spec в `plans/`, но добавить ссылки из `docs/architecture/*` на соответствующие спеки.
- [ ] Обновить `systemPatterns.md` (через Memory Bank updater) только если появился новый устойчивый паттерн.
- [ ] Обновить `README.md` или `docs/setup.md` при необходимости (если «каноническая точка входа» изменилась).

## Definition of Done

- [ ] В `docs/architecture/*` есть отражение ключевых принятых и реализованных решений.
- [ ] ADR созданы там, где есть триггеры (новые контракты/границы/инварианты).
- [ ] Ссылки на планы/задачи точечные и воспроизводимые.

## Execution Status

- Current State:
  - Добавлена инвентаризация (таблица plan → tasks → verification → SoT → status).
  - Созданы канонические архитектурные страницы:
    - [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)
    - [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
  - Создано ADR по decision URL-prefix groups и group-aware models:
    - [`docs/adr/0017-url-prefix-groups-and-group-aware-models.md`](docs/adr/0017-url-prefix-groups-and-group-aware-models.md:1)
  - Обновлены ссылки в карте компонентов: [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
  - Начата зачистка зависимостей `docs/` от `plans/` и `tasks_descriptions/`:
    - обновлён suite: [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)
    - обновлён канонический документ env policy: [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)
  - Верификация кода (на момент миграции):
    - `uv run python -m compileall api auth core services main.py tests` (ok)
    - `uv run python -m unittest discover -s tests -p "test_*.py"` (`Ran 31 tests`, `OK`)

- Next Step:
  - Полностью убрать из `docs/` оставшиеся ссылки на `plans/` и `tasks_descriptions/` (поиск: `regex=(plans/|tasks_descriptions/)`).

- Blockers: none
- Contract Changes: present
- Verification:
  - `uv run python -m compileall api auth core services main.py tests`
  - `uv run python -m unittest discover -s tests -p "test_*.py"`

## Handoff Notes

### What is done
- Канон (self-contained):
  - Quota rotation + groups: [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)
  - OpenAI chat_completions pipeline: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
- ADR:
  - URL-prefix groups + group-aware models: [`docs/adr/0017-url-prefix-groups-and-group-aware-models.md`](docs/adr/0017-url-prefix-groups-and-group-aware-models.md:1)
- Навигация:
  - Component map updated: [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
- Начата зачистка ссылок на `plans/` / `tasks_descriptions/`:
  - Suite updated: [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)
  - Env policy updated: [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)
- Инвентаризация добавлена в этот task-файл: [`tasks_descriptions/tasks/023-migrate-implemented-plans-to-architecture-docs.md`](tasks_descriptions/tasks/023-migrate-implemented-plans-to-architecture-docs.md:1)

### Immediate fix first
- Завершить зачистку `docs/` от ссылок на `plans/` и `tasks_descriptions/` (оставшиеся кандидаты на момент handoff):
  - [`docs/testing/suites/proxy-routes.md`](docs/testing/suites/proxy-routes.md:1)
  - [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1)
  - [`docs/testing/suites/quota-parity.md`](docs/testing/suites/quota-parity.md:1)
  - [`docs/testing/suites/config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md:1)
  - [`docs/adr/0014-stream-state-container-and-429-rotation-policy.md`](docs/adr/0014-stream-state-container-and-429-rotation-policy.md:1)

### Pending work
- Обновить `docs/` так, чтобы не осталось ни одной ссылки на `plans/` и `tasks_descriptions/`.
- Провести mini `architect-stage-review` (warn-only) по DoD checklist и зафиксировать verdict.
- После зачистки ссылок: удалить только реализованные на текущий момент артефакты из `plans/` и `tasks_descriptions/` (пакет удаления согласовать отдельно).

### Commands to run
- `uv run python -m compileall api auth core services main.py tests`
- `uv run python -m unittest discover -s tests -p "test_*.py"`

### User constraints
- Канонические документы должны быть самодостаточными.
- В `docs/` не должно остаться ссылок на `plans/` и `tasks_descriptions/`.
- Удаление выполняем только для уже реализованного на момент времени функционала.
- Оформление по канонам Architect stage: [`architect-stage`](../../../../home/anton-admin/.kilocode/skills-architect/architect-stage/SKILL.md:1) + gate [`architect-stage-review`](../../../../home/anton-admin/.kilocode/skills-architect/architect-stage-review/SKILL.md:1)


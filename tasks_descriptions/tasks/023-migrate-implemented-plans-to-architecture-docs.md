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

- Current State: task создан, инвентаризация не выполнена.
- Next Step: составить таблицу планов из [`plans/`](plans/018-refactor-p1-architecture.md:1) с пометками implemented/accepted/draft.
- Blockers: none
- Contract Changes: none
- Verification: manual review (docs consistency)


# Task: Спроектировать тесты для rotation policies (random + by-N) + групп аккаунтов + group-aware /v1/models

## Контекст
- Должно сопровождать реализацию: [`tasks_descriptions/tasks/021-rotation-policies-groups-and-models.md`](tasks_descriptions/tasks/021-rotation-policies-groups-and-models.md:1)
- Архитектурная спецификация: [`plans/015-016-account-rotation-architecture.md`](plans/015-016-account-rotation-architecture.md:1)

## Architecture Context References
- [x] [`plans/015-016-account-rotation-architecture.md`](plans/015-016-account-rotation-architecture.md:1)
- [x] [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Specification References
- [x] [`tasks_descriptions/tasks/015-random-account_rotation.md`](tasks_descriptions/tasks/015-random-account_rotation.md:1)
- [x] [`tasks_descriptions/tasks/016-account-rotation-by-n-queries.md`](tasks_descriptions/tasks/016-account-rotation-by-n-queries.md:1)

## Test Design References
- [x] Existing suite context: [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)

## Workflow References
- [x] none

## Цель
- Подготовить test design (L1–L4) и coverage matrix для разработки из задачи 021.

## Шаги реализации
- [x] Создать/обновить suite-документ под новые возможности (возможно расширить существующий): [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)
- [x] Зафиксировать новые test cases:
  - random-order (детерминировать через patch RNG)
  - by-N (ровно N успехов -> switch)
  - group isolation (g0 vs g1 vs g2, state независим)
  - group-aware `/v1/models`
  - all-cooldown error message `all accounts on cooldown please wait <seconds>`
- [x] Обновить индекс: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- [x] Подготовить конкретные команды верификации для dev (unittest, smoke).

## Definition of Done
- [x] Есть документ test design с трассировкой requirement -> suite -> test scripts
- [x] Есть список конкретных тестовых файлов, которые должны быть изменены/добавлены
- [x] Test-map обновлён

## Execution Status
- Current State: test design согласован (TC + levels + coverage matrix), suite/test-map обновлены.
- Next Step: в Code stage реализовать изменения из [`tasks_descriptions/tasks/021-rotation-policies-groups-and-models.md`](tasks_descriptions/tasks/021-rotation-policies-groups-and-models.md:1) и добавить/обновить тесты согласно coverage matrix в [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1).
- Blockers: none
- Contract Changes: none
- Verification: `uv run python -m unittest discover -s tests -p "test_*.py"`

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
- [ ] Создать/обновить suite-документ под новые возможности (возможно расширить существующий): [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)
- [ ] Зафиксировать новые test cases:
  - random-order (детерминировать через patch RNG)
  - by-N (ровно N успехов -> switch)
  - group isolation (g0 vs g1 vs g2, state независим)
  - group-aware `/v1/models`
  - all-cooldown error message `all accounts on cooldown please wait <seconds>`
- [ ] Обновить индекс: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- [ ] Подготовить конкретные команды верификации для dev (unittest, smoke).

## Definition of Done
- [ ] Есть документ test design с трассировкой requirement -> suite -> test scripts
- [ ] Есть список конкретных тестовых файлов, которые должны быть изменены/добавлены
- [ ] Test-map обновлён

## Execution Status
- Current State: task создан, test design не выполнен.
- Next Step: определить suite-структуру и список тест-кейсов.
- Blockers: none
- Contract Changes: none
- Verification: not started


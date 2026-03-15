# Task: Реализовать rotation policies (random + by-N) + группы аккаунтов + group-aware /v1/models

## Контекст
- Источник требований: [`tasks_descriptions/tasks/015-random-account_rotation.md`](tasks_descriptions/tasks/015-random-account_rotation.md:1), [`tasks_descriptions/tasks/016-account-rotation-by-n-queries.md`](tasks_descriptions/tasks/016-account-rotation-by-n-queries.md:1)
- Архитектурная спецификация: [`plans/015-016-account-rotation-architecture.md`](plans/015-016-account-rotation-architecture.md:1)

Цель изменений — расширить quota account-rotation:
- random порядок в rounding;
- переключение аккаунта после N успешных запросов (by-N);
- группы аккаунтов (изолированный state/счетчики) с URL-prefix вариантом B: `/{group_id}/v1/*`;
- `GET /v1/models` должен стать group-aware: модели берём из конфига группы.

## Architecture Context References
- [x] [`plans/015-016-account-rotation-architecture.md`](plans/015-016-account-rotation-architecture.md:1)
- [x] [`systemPatterns.md`](.kilocode/rules/memory-bank/systemPatterns.md:1)

## Specification References
- [x] [`tasks_descriptions/tasks/015-random-account_rotation.md`](tasks_descriptions/tasks/015-random-account_rotation.md:1)
- [x] [`tasks_descriptions/tasks/016-account-rotation-by-n-queries.md`](tasks_descriptions/tasks/016-account-rotation-by-n-queries.md:1)

## Test Design References
- [ ] Test Design task: [`tasks_descriptions/tasks/022-test-design-rotation-policies-groups-and-models.md`](tasks_descriptions/tasks/022-test-design-rotation-policies-groups-and-models.md:1)
- [ ] Existing suite context: [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)

## Workflow References
- [x] none

## Цель
- Реализовать политики ротации и группировки аккаунтов согласно спецификации, сохранив backward compatibility.

## Шаги реализации
- [ ] Обновить router ключи: `gemini -> gemini_cli`, `qwen -> qwen_code` (в коде стратегии и конфиг-роутере).
- [ ] Расширить парсинг accounts-config в [`services/account_router.py`](services/account_router.py:1):
  - добавить поддержку `rotation_policy.random_order` и `rotation_policy.rotate_after_n_successes`.
  - добавить поддержку `groups.<gid>.accounts` и `groups.<gid>.models`.
  - обеспечить default поведение: если `groups` отсутствует, работаем как `g0` с `all_accounts`.
- [ ] Реализовать random-order для rounding (выбор следующего аккаунта не по порядку в файле, но с учетом cooldown/exhausted).
- [ ] Реализовать by-N: после `N` успешных запросов на аккаунте переключаться на следующий доступный.
- [ ] Поведение all-cooldown: возвращать `429` с сообщением `all accounts on cooldown please wait <seconds>`.
- [ ] Реализовать URL-prefix groups (вариант B) на уровне Flask routes для OpenAI endpoints:
  - `POST /v1/chat/completions` (group=g0)
  - `POST /<group_id>/v1/chat/completions`
  - `GET /v1/models` (group=g0)
  - `GET /<group_id>/v1/models`
- [ ] Сделать `/v1/models` group-aware: выдавать модели из `groups.<gid>.models`.
- [ ] Обновить примеры конфигов: [`docs/examples/gemini_accounts_config.example.json`](docs/examples/gemini_accounts_config.example.json:1), [`docs/examples/qwen_accounts_config.example.json`](docs/examples/qwen_accounts_config.example.json:1).

## Definition of Done
- [ ] Реализация соответствует [`plans/015-016-account-rotation-architecture.md`](plans/015-016-account-rotation-architecture.md:1)
- [ ] Добавлены/обновлены тесты согласно test design (см. задачу 022)
- [ ] Пройдены проверки: `uv run python -m compileall ...`, `uv run python -m unittest discover -s tests -p "test_*.py"`
- [ ] Документация и примеры конфигов обновлены

## Execution Status
- Current State: task создан, реализация не начиналась.
- Next Step: выполнить test design (см. задача 022) и затем приступить к изменениям в [`services/account_router.py`](services/account_router.py:1).
- Blockers: none
- Contract Changes: none
- Verification: not started


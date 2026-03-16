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
- Current State: реализованы rotation policies (random + by-N), группы и group-aware `/v1/models`, добавлены тесты; проверки `compileall` и `unittest` проходят.
- Next Step: обновить примеры конфигов в [`docs/examples/gemini_accounts_config.example.json`](docs/examples/gemini_accounts_config.example.json:1) и [`docs/examples/qwen_accounts_config.example.json`](docs/examples/qwen_accounts_config.example.json:1) под новые поля `groups` и `rotation_policy`.
- Blockers: none
- Contract Changes: present
- Verification:
  - `uv run python -m compileall api auth core services main.py tests` (ok)
  - `uv run python -m unittest discover -s tests -p "test_*.py"` (ok)

## Handoff Notes
- What is done:
  - Реализованы новые поля и логика ротации в [`services/account_router.py`](services/account_router.py:1) (random-order, by-N, группы, all-cooldown wait-seconds).
  - Добавлены group-prefixed маршруты и group-aware `/v1/models` в [`api/openai/routes.py`](api/openai/routes.py:1).
  - Протянут `group_id` через контекст запроса в [`api/openai/pipeline.py`](api/openai/pipeline.py:83) и [`api/openai/types.py`](api/openai/types.py:8).
  - Обновлена стратегия ротации и обработка all-cooldown в [`api/openai/strategies/rotate_on_429_rounding.py`](api/openai/strategies/rotate_on_429_rounding.py:30).
  - Обновлён gemini native proxy для новых provider ids и cooldown-message в [`api/gemini/routes.py`](api/gemini/routes.py:46).
  - Добавлены тесты: router L1 в [`tests/test_quota_account_router.py`](tests/test_quota_account_router.py:17), group-aware `/v1/models` в [`tests/test_refactor_p2_routes.py`](tests/test_refactor_p2_routes.py:77), all-cooldown contract в [`tests/test_openai_contract.py`](tests/test_openai_contract.py:39).
  - Верификация: `compileall` и `unittest` успешно выполнены.
- Immediate fix first:
  - Обновить примеры конфигов в [`docs/examples/gemini_accounts_config.example.json`](docs/examples/gemini_accounts_config.example.json:1) и [`docs/examples/qwen_accounts_config.example.json`](docs/examples/qwen_accounts_config.example.json:1).
- Pending work:
  - Привести docs/examples в соответствие с `groups` и `rotation_policy`.
- Commands to run:
  - `uv run python -m compileall api auth core services main.py tests`
  - `uv run python -m unittest discover -s tests -p "test_*.py"`
- User constraints:
  - Используем `uv` для проверок.
  - Сохраняем OpenAI-compatible контракт и quota-first поведение.

## Implementation Handoff (для Code stage)

Канонический test design и coverage matrix: [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1).

### 1) Изменения в доменной логике ротации (L1)
Центральная точка: [`services/account_router.py`](services/account_router.py:1)

Ожидаемые изменения:
- Provider IDs в quota-роутере и стратегиях: `gemini`→`gemini_cli`, `qwen`→`qwen_code`.
- Расширить парсинг accounts-config:
  - `rotation_policy.random_order: bool` (default false)
  - `rotation_policy.rotate_after_n_successes: int` (default 0)
  - `groups.<gid>.accounts: list[str]`
  - `groups.<gid>.models: list[str]`
  - default: если `groups` отсутствует — работаем как `g0` с пулом `all_accounts`.
- Group isolation: ключ state должен стать `(provider, group_id)` вместо одного `provider`.
- Random-order:
  - при switch (429 / by-N) выбирать следующий аккаунт случайно среди доступных кандидатов (не exhausted и не cooldown), детерминируемо тестами через patch RNG.
- Rotate-after-N-successes:
  - хранить счётчик успешных запросов на аккаунте в state,
  - при достижении `N` триггерить switch на следующий доступный (и учитывать `random_order` если включён).
- All-cooldown fast-fail:
  - при невозможности выбрать аккаунт из-за cooldown вернуть 429 с message `all accounts on cooldown please wait <seconds>`,
  - `<seconds>` = время до ближайшего `cooldown_until` (ceil/округление зафиксировать в тесте).

### 2) Изменения в API (L2/L3)
Маршруты OpenAI:
- Добавить URL-prefix для групп (вариант B) для:
  - `POST /<group_id>/v1/chat/completions`
  - `GET /<group_id>/v1/models`
  - при этом сохранить `POST /v1/chat/completions` и `GET /v1/models` как default `g0`.

Ожидаемая точка модификации: [`api/openai/routes.py`](api/openai/routes.py:1)

Group-aware models:
- `GET /v1/models` и `GET /<group_id>/v1/models` должны возвращать модели из `groups.<gid>.models` (union по провайдерам группы).
- Backward compatibility: если `groups` отсутствует в accounts-config — поведение не ломается (допускается fallback к текущему поведению по availability, как эквивалент `g0`).

### 3) Тесты (что должно быть добавлено/обновлено)
- L1 router unit: [`tests/test_quota_account_router.py`](tests/test_quota_account_router.py:1)
  - TC-RAND-1/2, TC-N-1/2, TC-GRP-1, TC-CD-1 (см. suite).
- L3 routes: [`tests/test_refactor_p2_routes.py`](tests/test_refactor_p2_routes.py:1)
  - TC-MODELS-1/2: `GET /g1/v1/models` vs `GET /g2/v1/models`.
- L2/L3 contract: [`tests/test_openai_contract.py`](tests/test_openai_contract.py:1)
  - TC-CD-2: 429 all-cooldown message с `please wait <seconds>`.

# Suite: Unified quota account rotation (random + by-N + groups + group-aware models)

## Scope
Базовый контур (существующий):
- Выбор аккаунта в режиме `single` через `active_account`.
- Переключение в режиме `rounding` с раздельной реакцией на `rate_limit` (cooldown) и `quota_exhausted` (exhausted-until).
- Состояния `all_accounts_on_cooldown` и `all_accounts_exceed_quota`.
- Сохранение OpenAI stream/non-stream контракта при ротации.

Расширение (по задачам rotation policies + groups):
- Random-order в `rounding` (опция `rotation_policy.random_order`).
- Rotate-after-N-successes в `rounding` (опция `rotation_policy.rotate_after_n_successes`).
- Группы аккаунтов, изоляция state/счётчиков по ключу `(provider, group_id)`.
- URL-prefix groups (вариант B): `/<group_id>/v1/*` при сохранении default `g0` на `/v1/*`.
- Group-aware `GET /v1/models` и `GET /<group_id>/v1/models` (модели берём из `groups.<gid>.models`).
- All-cooldown fast-fail: `429` с message вида `all accounts on cooldown please wait <seconds>`.

## Contract References
- 429 error contract (reference): [`docs/contracts/api/openai/errors/429-error.schema.json`](../../contracts/api/openai/errors/429-error.schema.json)

Примечание: фактическая проверка контракта для этих сценариев выполняется через OpenAI-compatible envelope и ожидания по status/message в тестах уровня L2/L3.

## Requirement Traceability
### Requirements (нормализованные идентификаторы)
- REQ-015-RANDOM: random-order switching в `rounding`.
- REQ-016-BY-N: rotate-after-N-successes (by-N) в `rounding`.
- REQ-GRP-ISO: group isolation (state изолирован между группами).
- REQ-MODELS-GROUP: group-aware models endpoint.
- REQ-COOLDOWN-WAIT: all-cooldown message `please wait <seconds>`.
- REQ-RESET-PERIOD: period-based quota reset через `model_quota_resets` в формате `DD:HH:MM`.
- REQ-STATE-PERSIST: persisted exhausted state переживает рестарт процесса.
- REQ-DISJOINT-GROUPS: аккаунт может быть только в одной группе.
- REQ-QWEN-IDLE-REFRESH: Qwen refresh по idle-threshold и retry на 401/403.

### Source links
- Канонический архитектурный документ: [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)
- ADR по URL-prefix groups и group-aware models: [`docs/adr/0017-url-prefix-groups-and-group-aware-models.md`](docs/adr/0017-url-prefix-groups-and-group-aware-models.md:1)
- Реализация: [`services/account_router.py`](services/account_router.py:1)

## Risk Register (test-focused)
- RISK-1 (RNG nondeterminism): random-order требует детерминирования через patch RNG (например patch `random.choice`).
- RISK-2 (time dependency): cooldown/exhausted зависят от `time.time()`; тесты должны фиксировать время (patch time) и проверять вычисление `wait_seconds`.
- RISK-3 (file state): появится файловое состояние `secrets/<provider>/state/*`; тесты должны быть изолированы через temp dir.
- RISK-4 (breaking change): `model_quota_resets` больше не `HH:MM`.

## Test Levels (L1–L4)
- L1 Unit: чистая логика роутера (изменения в [`services/account_router.py`](services/account_router.py)), без Flask.
- L2 Contract: структура OpenAI-compatible ответов в части status/message для 429 сценариев (через Flask client в контрактных тестах).
- L3 Integration: маршрутизация Flask и group-aware endpoints (`/v1/*` vs `/<group_id>/v1/*`), без реальных upstream вызовов (моки провайдеров/роутера).
- L4 E2E: реальные upstream провайдеры (out of scope для этой suite).

## Test Cases (Given/When/Then)

### REQ-015-RANDOM (random-order)
- TC-RAND-1 (L1): Given `mode=rounding`, `random_order=true`, часть аккаунтов на cooldown, When происходит switch (через register_event), Then следующий аккаунт выбирается RNG среди доступных (детерминируем через patch RNG).
- TC-RAND-2 (L1): Given один аккаунт exhausted для model X, When switch, Then RNG не выбирает exhausted.

### REQ-016-BY-N (rotate-after-N-successes)
- TC-N-1 (L1): Given `rotate_after_n_successes=N`, When N раз регистрируем success на текущем аккаунте, Then следующий `select_account()` приводит к переключению.
- TC-N-2 (L1): Given by-N включён, When возникает 429 RATE_LIMIT/QUOTA_EXHAUSTED, Then 429-политика имеет приоритет (switch/cooldown/exhausted), а счётчик успехов не приводит к неконсистентности (best-effort).

### REQ-GRP-ISO (group isolation)
- TC-GRP-1 (L1): Given две группы `g1` и `g2` с разными пулами, When в `g1` происходит switch (429 или by-N), Then state `g2` не изменяется (ожидаем key state `(provider, group_id)`).

### REQ-MODELS-GROUP (group-aware /v1/models)
- TC-MODELS-1 (L3): Given accounts-config с `groups.g1.models=[m1]`, `groups.g2.models=[m2]`, When `GET /g1/v1/models`, Then только `m1`; When `GET /g2/v1/models`, Then только `m2`.
- TC-MODELS-2 (L3): Given `groups` отсутствует, When `GET /v1/models`, Then backward-compatible поведение: эквивалент `g0` (без префикса) и модели берутся как для `g0`.

### REQ-COOLDOWN-WAIT (all-cooldown please wait)
- TC-CD-1 (L1): Given все аккаунты на cooldown с разными `cooldown_until`, When `select_account()` не может выбрать, Then ошибка содержит `wait_seconds = min(cooldown_until) - now` (округление/ceil фиксируется в тесте).
- TC-CD-2 (L2/L3): When quota rounding path возвращает all-cooldown, Then HTTP `429` и `error.message` содержит `all accounts on cooldown please wait <seconds>`.

### REQ-RESET-PERIOD (period-based quota reset)
- TC-PERIOD-1 (L1): Given `model_quota_resets.default="01:00:00"`, When фиксируем `quota_exhausted_at=now`, Then exhausted-until вычисляется как `now + 86400`.

### REQ-STATE-PERSIST (persisted exhausted state)
- TC-STATE-1 (L1): Given persisted `quota_exhausted_at` на аккаунт+модель, When создаём новый router instance (симуляция рестарта), Then select_account() уважает exhausted до истечения периода.

### REQ-DISJOINT-GROUPS
- TC-DISJOINT-1 (L1): Given `groups` с пересечением account’ов, When load config, Then config error.

### REQ-QWEN-IDLE-REFRESH
- TC-QWEN-REFRESH-1 (L1/L2): Given `last_used_at` старше threshold, When делаем запрос, Then refresh вызывается.
- TC-QWEN-REFRESH-2 (L2): Given upstream 401/403, When запрос, Then refresh + retry один раз.

## Coverage Matrix
| Requirement | Test cases | Level | Target scripts |
| :--- | :--- | :---: | :--- |
| REQ-015-RANDOM | TC-RAND-1, TC-RAND-2 | L1 | `tests/test_quota_account_router.py` |
| REQ-016-BY-N | TC-N-1, TC-N-2 | L1 | `tests/test_quota_account_router.py` |
| REQ-GRP-ISO | TC-GRP-1 | L1 | `tests/test_quota_account_router.py` |
| REQ-MODELS-GROUP | TC-MODELS-1, TC-MODELS-2 | L3 | `tests/test_refactor_p2_routes.py` |
| REQ-COOLDOWN-WAIT | TC-CD-1, TC-CD-2 | L1 + L2/L3 | `tests/test_quota_account_router.py`, `tests/test_openai_contract.py` |
| REQ-RESET-PERIOD | TC-PERIOD-1 | L1 | `tests/test_quota_account_router.py` |
| REQ-STATE-PERSIST | TC-STATE-1 | L1 | `tests/test_quota_account_router.py` |
| REQ-DISJOINT-GROUPS | TC-DISJOINT-1 | L1 | `tests/test_quota_account_router.py` |
| REQ-QWEN-IDLE-REFRESH | TC-QWEN-REFRESH-1, TC-QWEN-REFRESH-2 | L1/L2 | `tests/test_openai_contract.py` |

## Scripts
- Router unit: `tests/test_quota_account_router.py`
- Routes smoke/integration: `tests/test_refactor_p2_routes.py`
- OpenAI-compatible contract: `tests/test_openai_contract.py`

## Verification Command
- `uv run python -m unittest tests/test_quota_account_router.py`
- `uv run python -m unittest tests/test_refactor_p2_routes.py`
- `uv run python -m unittest tests/test_openai_contract.py`
- Full run: `uv run python -m unittest discover -s tests -p "test_*.py"`

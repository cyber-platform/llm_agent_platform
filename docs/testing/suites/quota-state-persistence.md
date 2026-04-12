# Suite: Quota state persistence (STATE_DIR + account_state.json + group snapshot + async writer)

## Suite ID
- `TS-QUOTA-STATE-PERSISTENCE`

## Documentation roots
- `docs/testing/test-map.md`
- `docs/testing/traceability.md`
- `docs/testing/suites/quota-state-persistence.md`

## Implementation roots
- `services/backend/llm_agent_platform/tests/test_quota_account_router.py`
- planned `services/backend/llm_agent_platform/tests/test_quota_state_persistence.py`

## Search anchors
- `TS-QUOTA-STATE-PERSISTENCE`
- `test_quota_account_router.py`
- `TC-STATE-`
- `STATE_DIR`

## Scope

Покрываем изменения в quota-first контуре, связанные с persisted runtime state и мониторинговым snapshot.

В рамках suite тестируем:

- новый persisted account state формат `account_state.json`
- `LLM provider`-specific account artifacts `usage_windows.json` и `request_usage.json`
- новый layout под `STATE_DIR` (state на HDD)
- восстановление in-memory состояния роутера при старте из файлов
- `quota_scope: per_model | per_provider`
- async writer (coalesce map) и его свойства: swap + merge-back
- генерацию group snapshot `quota_state.json` (только числа/доли)

Non-scope:

- реальные OAuth токены/real upstream
- производительность на больших пулах аккаунтов (можно добавить позже как perf note)

## Architecture References

- [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
- База quota rotation: [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)
- Persisted reset periods (история): [`docs/architecture/quota-reset-periods-and-account-state.md`](docs/architecture/quota-reset-periods-and-account-state.md:1)
- Теория coalesce map: [`docs/theory/coalesce-map.md`](docs/theory/coalesce-map.md:1)

## Requirement Traceability

- Suite rollout note: suite-level anchor уже каноничен как `TS-QUOTA-STATE-PERSISTENCE`; existing requirement and case identifiers сохраняются как legacy-compatible anchors до отдельной нормализации.

### Requirements

- REQ-STATE-DIR: state-файлы пишутся/читаются из `STATE_DIR`, secrets остаются в `secrets/`.
- REQ-ACCOUNT-STATE-V1: единый файл `account_state.json` содержит `last_used_at`, `cooldown.last_cooldown_at`, `quota_exhausted.keys`.
- REQ-USAGE-WINDOWS-V1: `LLM provider`-specific monitoring snapshot хранится в `usage_windows.json` и пишет refresh metadata отдельно от request counters.
- REQ-REQUEST-USAGE-V1: request-driven observability хранится в `request_usage.json` и не перетирает monitoring windows.
- REQ-LAZY-HYDRATE: при первом доступе к `(provider_id, group_id)` runtime восстанавливает in-memory state из `STATE_DIR` (lazy hydrate = lazy restore persisted state) без обязательного глобального pre-scan.
- REQ-COOLDOWN-RESTORE: cooldown переживает рестарт (восстанавливается из `last_cooldown_at`).
- REQ-QUOTA-SCOPE: `LLM provider` accounts-config поддерживает `quota_scope=per_model|per_provider`.
- REQ-PROVIDER-SENTINEL: для `per_provider` используется ключ `__provider__`.
- REQ-GROUP-SNAPSHOT: пишется snapshot `quota_state.json` для `(provider_id, group_id)` и содержит только числа/доли.
- REQ-ASYNC-WRITER: запись state на диск async, периодический flush.
- REQ-WRITER-SWAP: writer flush делает swap `pending -> to_flush`.
- REQ-WRITER-MERGEBACK: при ошибке записи writer merge-back `to_flush` в `pending` без затирания более свежих значений.
- REQ-WRITER-SHUTDOWN: при graceful shutdown writer делает best-effort final flush.

## Risk Register (test-focused)

- RISK-TIME: cooldown/exhausted зависят от времени — нужен patch времени.
- RISK-FS: тесты не должны писать в реальные директории — нужен temp dir для `STATE_DIR`.
- RISK-RACE: async writer конкурентный — тесты должны быть детерминированными (например, вручную дергать flush без real thread).

## Test Levels (L1–L4)

- L1 Unit: логика вычислений и восстановлений (router/state store/writer), без Flask.
- L2 Contract: валидация форматов state файлов (внутренние JSON contracts) и поведения ошибок.
- L3 Integration: smoke через Flask (если потребуется) только для подтверждения, что новое состояние не ломает API.
- L4 E2E: out of scope.

## Test Cases (Given/When/Then)

### REQ-STATE-DIR

- TC-STATE-DIR-1 (L1): Given `STATE_DIR=/tmp/...`, When writer пишет `account_state.json`, Then файл появляется под `STATE_DIR/<provider>/accounts/<account>/account_state.json`.

### REQ-ACCOUNT-STATE-V1

- TC-ASTATE-1 (L1): Given `account_state.json` c `quota_exhausted.keys`, When router восстанавливает состояние из файла (hydrate), Then router считает exhausted корректно.

### REQ-USAGE-WINDOWS-V1 + REQ-REQUEST-USAGE-V1

- TC-UPROV-1 (L1): Given `LLM provider` monitoring refresh обновляет usage snapshot, When persisted payload materialized, Then `usage_windows.json` содержит два окна и refresh metadata.
- TC-UPROV-2 (L1): Given request-path usage update, When persisted payload materialized, Then `request_usage.json` обновляется отдельно и не затирает `usage_windows.json`.

### REQ-LAZY-HYDRATE

- TC-HYDRATE-1 (L1): Given в `STATE_DIR` уже есть `account_state.json`, When первый вызов роутера обращается к `(provider_id, group_id)`, Then in-memory state lazily восстанавливается из файлов без отдельного bootstrap scan API.

### REQ-COOLDOWN-RESTORE

- TC-CD-RESTORE-1 (L1): Given `last_cooldown_at = now - 1s` и `rate_limit_cooldown_seconds=5`, When restart+hydrate, Then аккаунт считается в cooldown.
- TC-CD-RESTORE-2 (L1): Given `last_cooldown_at = now - 10s` и `rate_limit_cooldown_seconds=5`, Then аккаунт не в cooldown.

### REQ-QUOTA-SCOPE + REQ-PROVIDER-SENTINEL

- TC-QSCOPE-1 (L1): Given `quota_scope=per_provider`, When фиксируем exhausted по модели `m1`, Then запись/проверка использует key `__provider__`.
- TC-QSCOPE-2 (L1): Given `quota_scope=per_model`, When exhausted по `m1`, Then запись/проверка использует key `m1`.

### REQ-GROUP-SNAPSHOT

- TC-SNAP-1 (L1): Given группа из N аккаунтов и часть в cooldown, When snapshot, Then `total_accounts=N`, `cooldown_accounts=K`, `cooldown_ratio=K/N`.
- TC-SNAP-2 (L1): Given `quota_scope=per_model`, When snapshot для `models.<m>`, Then `exhausted_accounts` корректен для модели.

### REQ-ASYNC-WRITER + SWAP + MERGEBACK

- TC-WRITER-1 (L1): Given pending содержит `{p1: v1}`, When flush делает swap, Then новые enqueue идут в новый pending и не теряются.
- TC-WRITER-2 (L1): Given flush падает на записи, When merge-back, Then старые `to_flush` возвращаются в pending, но более свежие значения не затираются.
- TC-WRITER-3 (L1): Given pending содержит незаписанные payloads, When вызывается graceful shutdown / close writer, Then выполняется final flush best-effort.

## Coverage Matrix

| Requirement | Test cases | Level | Target scripts |
| :--- | :--- | :---: | :--- |
| REQ-STATE-DIR | TC-STATE-DIR-1 | L1 | `tests/test_quota_account_router.py` (или новый `tests/test_quota_state_persistence.py`) |
| REQ-ACCOUNT-STATE-V1 | TC-ASTATE-1 | L1 | то же |
| REQ-USAGE-WINDOWS-V1 | TC-UPROV-1 | L1 | то же |
| REQ-REQUEST-USAGE-V1 | TC-UPROV-2 | L1 | то же |
| REQ-LAZY-HYDRATE | TC-HYDRATE-1 | L1 | то же |
| REQ-COOLDOWN-RESTORE | TC-CD-RESTORE-1, TC-CD-RESTORE-2 | L1 | то же |
| REQ-QUOTA-SCOPE | TC-QSCOPE-1, TC-QSCOPE-2 | L1 | то же |
| REQ-GROUP-SNAPSHOT | TC-SNAP-1, TC-SNAP-2 | L1 | то же |
| REQ-WRITER-SWAP | TC-WRITER-1 | L1 | то же |
| REQ-WRITER-MERGEBACK | TC-WRITER-2 | L1 | то же |
| REQ-WRITER-SHUTDOWN | TC-WRITER-3 | L1 | то же |

## Verification Command

- `uv run python -m unittest discover -s tests -p "test_*.py"`

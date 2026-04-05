# ADR-0019: Breaking — `STATE_DIR`, unified `account_state.json`, group snapshot и async writer

- Status: Proposed
- Date: 2026-03-18
- Related:
  - [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
  - [`docs/architecture/quota-reset-periods-and-account-state.md`](docs/architecture/quota-reset-periods-and-account-state.md:1)
  - [`docs/adr/0018-quota-reset-periods-and-account-state.md`](docs/adr/0018-quota-reset-periods-and-account-state.md:1)

## Контекст

После фиксации persisted quota state в [`docs/adr/0018-quota-reset-periods-and-account-state.md`](docs/adr/0018-quota-reset-periods-and-account-state.md:1) обнаружились новые требования:

1. runtime state нужно вынести из `secrets/` в отдельную директорию с частой перезаписью на HDD;
2. cooldown должен переживать рестарт, а не жить только в памяти;
3. администратору нужен provider-group snapshot с агрегированной доступностью аккаунтов;
4. запись state не должна ухудшать request-path latency.

Текущий split-layout `last_used_at.json` + `quota_exhausted/<model>.json` больше не соответствует этим требованиям и усложняет восстановление состояния при старте.

## Решение

1. Вводится отдельный runtime state root:
   - `STATE_DIR` — optional runtime env;
   - code default: `/app/state`;
   - для production/container deployments переменная должна инжектиться явно и обычно монтироваться на HDD.

2. Persisted состояние аккаунта унифицируется в один файл:
   - `<STATE_DIR>/<provider_id>/accounts/<account_name>/account_state.json`;
   - файл содержит `last_used_at`, `cooldown.last_cooldown_at`, `quota_exhausted.keys`.

3. Для `(provider_id, group_id)` вводится monitoring snapshot:
   - `<STATE_DIR>/<provider_id>/groups/<group_id>/quota_state.json`;
   - snapshot содержит только агрегаты и доли, без списков аккаунтов.

4. В provider accounts-config вводится `quota_scope`:
   - `per_model`;
   - `per_provider`;
   - для `per_provider` используется sentinel key `__provider__`.

5. Запись runtime state выполняется асинхронно:
   - write-behind / last-write-wins buffer;
   - coalesce map `pending[path] = payload`;
   - periodic flush;
   - swap `pending -> to_flush`;
   - merge-back при write failure;
   - overflow policy: drop-oldest + warning log.

6. Hydrate состояния делается лениво при первом доступе к конкретному `(provider_id, group_id)` после старта процесса; глобальный pre-scan всего `STATE_DIR` не требуется.

7. Lifecycle writer:
   - background thread стартует лениво на первом `enqueue_write()`;
   - при graceful shutdown выполняется best-effort final flush;
   - при crash / SIGKILL допускается потеря последнего не-flushed хвоста state.

## Contract changes

- present

Контракты:
- Provider config: [`docs/contracts/config/provider-accounts-config.schema.json`](docs/contracts/config/provider-accounts-config.schema.json:1)
- Account state v1: [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1)
- Group quota snapshot v1: [`docs/contracts/state/group-quota-state.schema.json`](docs/contracts/state/group-quota-state.schema.json:1)

## Альтернативы

### A. Оставить state внутри `secrets/<provider>/state`
- Плюсы: меньше breaking changes.
- Минусы: смешение credentials и hot-write runtime state, неудобно выносить на HDD.

### B. Оставить split state layout по нескольким JSON файлам
- Плюсы: минимальный инкрементальный рефакторинг.
- Минусы: сложнее hydrate cooldown, больше файлов и директорий, хуже admin readability.

### C. Синхронная запись state на request-path
- Плюсы: проще reasoning по persistence.
- Минусы: лишний I/O в критическом пути и худшая tail latency.

## Последствия

### Позитивные
- Runtime state отделяется от credentials и лучше соответствует storage policy.
- Cooldown и exhausted переживают рестарт.
- Admin получает человеко-читаемый snapshot по group availability.
- Request-path остаётся in-memory-first.

### Негативные
- Breaking изменение state layout без миграции legacy файлов.
- Snapshot может отставать от последнего in-memory состояния.
- При crash можно потерять последний не-flushed хвост изменений.

## Условия пересмотра

- Если потребуется multi-process writer с межпроцессной координацией.
- Если понадобится строгая cross-file transactional consistency.
- Если monitoring snapshot станет operational source of truth, а не best-effort артефактом.

## Update (2026-04-05)

Provider-specific account monitoring artifacts и admin read-model boundary были расширены отдельным решением:

- добавлены `usage_windows.json` и `request_usage.json` как account-scoped provider artifacts;
- зафиксировано, что admin UI читает только backend read-model из in-memory state;
- public `429` surface сохранён отдельно от richer internal/admin taxonomy.

Это зафиксировано в [`docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md`](docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md:1).

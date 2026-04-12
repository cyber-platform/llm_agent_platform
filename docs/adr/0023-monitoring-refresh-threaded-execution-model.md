# ADR 0023: thread-based execution model for monitoring refresh runs in PoC

- Status: Accepted
- Date: 2026-04-12
- Related:
  - [`docs/architecture/admin-monitoring-refresh-subsystem.md`](docs/architecture/admin-monitoring-refresh-subsystem.md:1)

## Контекст

Manual refresh и background polling должны выполнять I/O-bound provider usage refresh tasks для нескольких accounts.

Current backend stack остаётся sync-first, а PoC не требует отдельной distributed job infrastructure.

## Решение

1. Refresh subsystem использует background threads внутри backend process.
2. Account refresh tasks исполняются через bounded thread pool.
3. Concurrency и timeout policy задаются backend service config, а не `.env`.
4. Completed run state хранится в process memory ограниченное время.

PoC defaults:

- `refresh_concurrency = 5`
- `per_account_refresh_timeout_seconds = 10`
- `refresh_run_timeout_seconds = 60`
- `refresh_run_retention_seconds = 300`

## Alternatives considered

### A. Separate worker process

- Плюсы: stronger isolation.
- Минусы: IPC, lifecycle coordination и extra complexity не окупаются в PoC.

### B. Asyncio-first orchestration

- Плюсы: хороша для ASGI/async-native stack.
- Минусы: текущий sync-first backend не выигрывает достаточно, чтобы оправдать mixed async model.

### C. External queue system

- Плюсы: durability и better scaling.
- Минусы: преждевременно для PoC и current scale.

## Последствия

### Положительные

- реализация fit-ится в существующий backend stack;
- bounded concurrency снижает риск over-polling upstream;
- operational tuning выносится в service config.

### Негативные

- execution model остаётся process-local;
- restart backend теряет in-flight refresh runs;
- future multi-instance deployment потребует пересмотра.

## Условия пересмотра

- Рост account count и latency beyond PoC assumptions.
- Переход backend на ASGI/async-first runtime.
- Появление durable job history, cancellation или distributed workers.

# Открытые вопросы по platform-wide monitoring runtime

## Контекст

В рамках PoC зафиксировано направление на memory-first monitoring runtime, где persisted artifacts используются только для restore after restart и audit trail, а frontend читает только backend in-memory read-model.

Текущий implementation scope остается ограничен `openai-chatgpt`.

## Зафиксированные open questions

### 1. Поведение при нескольких backend instances

- Current status: out of scope для текущего PoC.
- Почему это важно:
  - process-local in-memory monitoring store и refresh run registry перестают быть достаточными;
  - background pollers могут дублировать upstream refresh;
  - manual refresh duplicate-run reuse semantics ломается без shared coordination;
  - разные instances могут отдавать frontend разные refresh states.
- Что пока не freeze:
  - shared store vs distributed coordinator;
  - leader election / lease model;
  - durability и ownership для refresh runs;
  - consistency guarantees для admin read-model.
- Follow-up policy:
  - не расширять текущий PoC design до multi-instance assumptions без отдельной архитектурной переработки;
  - вернуться к вопросу после завершения single-instance PoC baseline.

### 2. Общий normalized monitoring contract для всех providers

- Current status: не входит в immediate implementation scope.
- Provisional decision:
  - пока допускаются только provider-specific page projections;
  - `openai-chatgpt` остается первым materialized provider;
  - generalized `monitoring_dimensions[]` проектируется отдельной задачей и не freeze-ится молча как обязательный universal contract.

### 3. Providers без polling-based monitoring API

- Current status: подтверждено, что у части providers доступна только request-derived observability.
- Architectural implication:
  - platform-wide monitoring runtime не должен предполагать, что каждый provider поддерживает background/manual upstream refresh;
  - capability matrix и page projection должны допускать providers без refreshable usage windows.

## Candidate revisit triggers

- появление multi-instance backend deployment;
- необходимость durable job history или cancel semantics;
- materialization второго и третьего providers в общем monitoring runtime;
- переход admin surface за пределы local single-user PoC boundary.

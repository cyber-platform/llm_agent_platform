# Discussion F-002: state ownership and write paths for `openai-chatgpt` monitoring

## Context

Этот документ закрывает замечание `F-002` из [`plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md`](plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md:35).

После решения `F-001` в [`plans/discussion-f-001-state-and-contract-boundary-openai-chatgpt-monitoring.md`](plans/discussion-f-001-state-and-contract-boundary-openai-chatgpt-monitoring.md:1) новый account-centric boundary уже принят как целевой канон. Для `F-002` осталось зафиксировать:

- ownership matrix по state artifacts
- единый write path policy
- роль persisted files в in-memory-first сервисе
- границу между live admin UI и backup state files

## Discovery scope

В этом finding решаются только вопросы ownership и write path semantics для:

- [`account_state.json`](docs/contracts/state/account-state.schema.json:1)
- [`quota_state.json`](docs/contracts/state/group-quota-state.schema.json:1)
- `usage_windows.json`
- `request_usage.json`

### Non-scope

Здесь не решаются:

- schema boundary этих файлов как contract-first артефактов, это уже продолжение `F-001`
- внешний `429` surface, это `F-003`
- semantics admin action `Activate`, это `F-004`

## Current baseline

### Current runtime reality

Сейчас фактическое состояние такое:

- router пишет account runtime state и group snapshot через [`QuotaAccountRouter.register_event()`](llm_agent_platform/services/account_router.py:274), [`QuotaAccountRouter.register_success()`](llm_agent_platform/services/account_router.py:206), [`QuotaAccountRouter._persist_account_state_unlocked()`](llm_agent_platform/services/account_router.py:701) и [`QuotaAccountRouter._enqueue_group_snapshot_unlocked()`](llm_agent_platform/services/account_router.py:737)
- monitoring adapter отдельно пишет usage snapshot синхронно через [`OpenAIChatGptUsageLimitsAdapter.write_snapshot()`](llm_agent_platform/services/provider_usage_limits.py:91)
- архитектурный канон persistence уже ожидает общий async write-behind подход через [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:222)

### Canon already fixed by platform docs

В платформенном каноне уже зафиксировано:

- runtime работает по in-memory state, а persisted state нужен для восстановления и асинхронной записи в [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:228)
- [`account_state.json`](docs/contracts/state/account-state.schema.json:1) — persisted router state
- [`quota_state.json`](docs/contracts/state/group-quota-state.schema.json:1) — monitoring snapshot и не source of truth для routing

### Ambiguity introduced by new plan

План [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:163) добавляет ещё два account-level файла:

- `usage_windows.json`
- `request_usage.json`

Но без явного решения оставались вопросы:

- кто их semantic owner
- кто имеет право писать их на диск
- должны ли они идти через единый async writer
- должен ли UI читать live state из памяти сервиса или из persisted snapshots
- являются ли persisted files fallback live source или только backup layer

## Why critic is correct

Critic прав по сути полностью.

Если оставить эту часть незафиксированной, то получится смесь несовместимых моделей:

1. router-class state с async persistence
2. monitoring snapshot со своим sync write path
3. request-usage state с ещё одним отдельным write path

Это создаёт:

- гонки между refresh path и request path
- разную freshness semantics для соседних файлов
- скрытое нарушение правила `one artifact = one owner`
- неочевидную модель для backend admin read-model и frontend

## Consolidated target model

Для `F-002` принимается единая целевая модель `Option D`.

### Core principles

1. Сервис работает **in-memory-first**.
2. Persisted files нужны только для `restore after restart` и `audit trail`.
3. Frontend не читает state files напрямую.
4. Backend admin API отдаёт contract-first read-model из in-memory состояния сервиса.
5. Все mutable state files пишутся только через общий async writer с coalesce semantics.
6. У каждого artifact есть один semantic owner.

## Clarifications fixed during discussion

### Provider modularity

Ownership model не должен быть привязан только к [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1).

Правильная модульная граница такая:

- provider-specific monitoring subsystem знает, как получать и нормализовать usage data конкретного provider
- provider-specific quota handler знает, как интерпретировать provider errors и monitoring hints
- strategy layer и router остаются provider-agnostic, насколько это возможно
- persistence layer не знает provider business semantics и только записывает already-prepared payloads

Следствие:

- у разных providers могут быть разные окна, лимиты, buckets, reset semantics и refresh cadence
- но ownership policy остаётся общей для платформы

### Strategy modularity

Стратегии account routing не должны становиться владельцами файлов напрямую.

Правильная граница:

- strategy принимает runtime decision
- router владеет routing state mutations
- monitoring subsystem владеет monitoring snapshot mutations
- request-usage collector владеет request observability state
- persistence layer только materializes state changes на диск

### In-memory-first service model

Согласованная модель сервиса:

- процесс стартует
- один раз гидрирует нужное persisted state из файлов
- дальше живёт только на in-memory state
- асинхронно пишет backup state обратно в файлы через coalesce map

То есть fallback live semantics не нужна.

Persisted files не рассматриваются как live source ни для runtime, ни для frontend.

### Frontend boundary

Фронтенд не должен читать state files напрямую.

Также frontend не должен зависеть от тайминга `enqueue` или `flush`.

Правильная граница:

- UI читает только backend admin API
- backend admin API строит read-model из in-memory runtime state и in-memory latest monitoring snapshot
- persisted files не участвуют в normal live delivery path к UI

Для PoC достаточно polling admin API.

Будущее расширение через SSE или WebSocket допустимо, но это evolution канала доставки admin read-model, а не изменение ownership model файлов.

### In-memory monitoring snapshot vs `coalesce map`

Это разные сущности.

- in-memory monitoring snapshot — последнее актуальное доменное monitoring state, которое может читать runtime или backend admin API
- `coalesce map` из [`docs/theory/coalesce-map.md`](docs/theory/coalesce-map.md:1) — технический write buffer для асинхронного flush на диск

Практическая разница:

- subsystem сначала обновляет in-memory snapshot
- затем enqueue-ит сериализованный payload в `coalesce map`
- runtime и backend admin API читают из in-memory состояния
- `coalesce map` не является reader-facing cache

## Ownership matrix

| Artifact | Semantic owner | Persistence path | Read side | Semantics |
| --- | --- | --- | --- | --- |
| [`account_state.json`](docs/contracts/state/account-state.schema.json:1) | router | только shared async writer | router hydrate, backend admin read-model | routing-critical persisted backup |
| [`quota_state.json`](docs/contracts/state/group-quota-state.schema.json:1) | router snapshot builder | только shared async writer | backend admin read-model | derived monitoring snapshot |
| `usage_windows.json` | monitoring refresh subsystem | только shared async writer | provider quota handler, backend admin read-model | latest provider usage snapshot |
| `request_usage.json` | runtime request-usage collector | только shared async writer | backend admin read-model | request-driven observability state |

## Lifecycle policy

### Forced refresh

- semantic initiator: provider-specific quota handler или monitoring scheduler
- allowed effect: обновить только `usage_windows.json`
- forbidden effect: напрямую писать [`account_state.json`](docs/contracts/state/account-state.schema.json:1) в обход router

### Startup warmup

- semantic initiator: monitoring subsystem
- allowed effect: best-effort refresh `usage_windows.json`
- forbidden effect: блокировать startup или самостоятельно мутировать router state

### Refresh on unblock

- semantic initiator: monitoring subsystem по достижении unblock threshold
- allowed effect: refresh `usage_windows.json`
- allowed integration: передать сигнал в router logic через отдельный API или call boundary
- forbidden effect: напрямую писать [`account_state.json`](docs/contracts/state/account-state.schema.json:1)

### Request path updates

- request path может обновлять `request_usage.json`
- request path не должен напрямую перетирать `usage_windows.json`
- request path не должен обходить router при изменении [`account_state.json`](docs/contracts/state/account-state.schema.json:1)

## Rejected directions

Следующие направления считаются неактуальными и не должны оставаться в downstream plans:

- mixed ownership с разными независимыми writer paths для соседних файлов
- sync-write special case для monitoring state как основной канон
- идея, что persisted files являются live source для frontend
- смешение in-memory monitoring snapshot и `coalesce map`
- чтение UI напрямую из файлового state

## Draft requirements

### US

- `US-F002-01`: как архитектор платформы, я хочу иметь явную ownership matrix по каждому state artifact, чтобы исполнители не вводили конкурирующие writer paths
- `US-F002-02`: как разработчик backend admin API, я хочу строить read-model из in-memory состояния сервиса, чтобы UI не зависел от гонок файлового flush
- `US-F002-03`: как оператор сервиса, я хочу видеть согласованное monitoring state без артефактов от случайного чтения persisted files между enqueue и flush

### NFR

- `NFR-F002-01`: каждый mutable state artifact имеет одного semantic owner
- `NFR-F002-02`: все mutable state files пишутся через shared async writer
- `NFR-F002-03`: persisted files используются только для restore after restart и audit trail
- `NFR-F002-04`: frontend получает state только через backend admin contract
- `NFR-F002-05`: forced refresh, startup warmup и refresh-on-unblock не создают альтернативный write path в тот же artifact

### CONS

- `CONS-F002-01`: routing truth остаётся отдельной от monitoring truth, как в [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:138)
- `CONS-F002-02`: [`quota_state.json`](docs/contracts/state/group-quota-state.schema.json:1) остаётся derived monitoring snapshot и не становится routing source of truth
- `CONS-F002-03`: решение должно быть совместимо с async writer canon из [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:239)

## Recommendation

Рекомендую окончательно заморозить `Option D` как accepted baseline для `F-002`.

### Why

Этот вариант:

- лучше всего согласуется с already accepted account-centric boundary из `F-001`
- сохраняет модульность по provider-specific monitoring и quota semantics
- удерживает сервис в чистой in-memory-first модели
- убирает UI из гонок чтения или записи файлов
- оставляет единый persistence law для всех mutable state artifacts

## Accepted decision

- Status: `accepted`
- Decision date: `2026-03-31`
- Accepted option: `Option D`

### Accepted statements

1. Runtime source of truth живёт только в memory.
2. Persisted files нужны только для восстановления состояния после рестарта и для audit trail.
3. Backend admin read-model строится из in-memory runtime state и in-memory latest monitoring snapshot.
4. Frontend не читает files напрямую и не зависит от file flush timing.
5. Все mutable state artifacts пишутся только через shared async writer с coalesce semantics.
6. `coalesce map` не является live cache для runtime или UI.
7. `usage_windows.json` и `request_usage.json` имеют разных semantic owners, но общий persistence path.
8. [`account_state.json`](docs/contracts/state/account-state.schema.json:1) меняется только router path.

### Consequences for plan rewrite

Теперь downstream plans нужно переписать так, чтобы в них больше не оставалось:

- sync-write assumptions как основного канона
- идеи file-based live monitoring для UI
- неоднозначности между latest in-memory state и persisted backup copies

Конкретно требуется:

- обновить [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:1), добавив ownership matrix, in-memory-first principle и lifecycle rules
- обновить [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:1), зафиксировав backend admin read-model как единственную границу для UI
- обновить [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:222), расширив async writer canon на provider-specific account artifacts
- подготовить implementation tasks на shared persistence extension и admin read-model

## Check: did we clarify everything for `F-002`

### Clarified and closed

В ходе обсуждения были закрыты все главные архитектурные вопросы finding:

- кто владеет каждым artifact
- нужен ли единый async writer
- как это согласуется с provider modularity
- как это согласуется со strategy modularity
- должны ли persisted files быть live source
- как frontend должен получать состояние
- чем отличается latest in-memory snapshot от [`coalesce map`](docs/theory/coalesce-map.md:1)

### Remaining open questions

Блокирующих open questions для `F-002` больше не осталось.

Остаются только downstream design details, которые не блокируют freeze этого finding:

1. точная форма contract-first admin read-model schema
2. конкретная техника доставки live updates в будущем: polling only или позже SSE or WebSocket
3. конкретная реализация shared persistence abstraction в runtime code

Эти вопросы уже не меняют принятое решение `F-002`, а относятся к следующему этапу переписывания plans и implementation design.

## Next finding

Следующий документ должен разбирать `F-003` из [`plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md`](plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md:53) про внешний OpenAI-compatible `429` surface и границу между internal/admin states и public API semantics.

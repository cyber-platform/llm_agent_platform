# LLM Provider Catalog

## Назначение

Этот индекс фиксирует актуальный список `LLM provider` pages и их свойства в рамках `LLM provider`-centric платформы.

Важно разделять два уровня:

- platform capability — что архитектура в целом умеет поддерживать;
- current `LLM provider` status — что реально канонизировано для конкретного `LLM provider` на текущем этапе.

Например, discovery-based catalogs и [`provider-catalog-snapshot`](docs/contracts/state/provider-catalog-snapshot.schema.json:1) остаются ожидаемой capability платформы, но это не означает, что каждый текущий `LLM provider` уже использует discovery lifecycle.

## LLM provider matrix

| LLM provider | Route namespace | Auth kind | Catalog kind | Usage-limits capability | Runtime readiness | Details |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `openai-chatgpt` | `/openai-chatgpt/v1/*` | OAuth-based runtime | static bootstrap catalog | reactive exhaustion detection + monitoring-only proactive usage polling for observability | Implemented | [`openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1) |

## Canonical capability semantics

### Catalogs
- Static bootstrap catalog — `LLM provider` использует только локальный bootstrap catalog как текущий Source of Truth.
- Discovery-capable catalog — `LLM provider` может использовать [`provider-catalog-snapshot`](docs/contracts/state/provider-catalog-snapshot.schema.json:1) и optional discovery refresh после отдельной архитектурной фиксации.

### Usage limits
- Reactive exhaustion detection — quota/exhaustion определяется по ошибкам runtime request path.
- Proactive usage polling — отдельный usage endpoint или другой способ получить usage snapshot; это optional capability `LLM provider` и используется только для observability и monitoring, а не как основной механизм quota enforcement.

### Runtime readiness
- Foundation only — зафиксированы route namespace, contracts и boundaries, но `provider implementation` ещё не реализован end-to-end.
- Implemented — `provider implementation` реализован и входит в активный runtime канон.

## Related documents

- Routing and catalogs ADR: [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1)
- Component map: [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
- `LLM provider`-specific page: [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)

# Documentation Index

## Назначение

Этот документ является главным navigation entry point для engineering documentation проекта `llm_agent_platform`.

`docs/` хранит канонический engineering Source of Truth для системы целиком: architecture, contracts, terms, testing и long-lived technical decisions.

## Documentation layers

- `docs/` — Engineering Documentation SoT для `llm_agent_platform`.
- `operational_scope/` — временный operational layer для tasks, plans, research, review, open questions и spike artifacts.
- Новое знание может рождаться в `operational_scope/`, но становится обязательным для команды только после канонизации в `docs/`.
- Если operational artifact конфликтует с `docs/`, приоритет у `docs/`.

## Карта разделов

| Раздел | Назначение | Entry point |
| --- | --- | --- |
| Overview | Product framing, system boundary и маршруты чтения. | [`vision.md`](./vision.md) |
| Architecture | System context, containers, components, runtime flows и architecture evidence. | [`index.md`](./architecture/index.md) |
| Services | Карта сервисов системы, repo boundaries и service ownership. | [`index.md`](./services/index.md) |
| Providers | Provider matrix и provider-specific behavior. | [`index.md`](./providers/index.md) |
| Configuration | Env layout, service config и provider accounts config. | [`index.md`](./configuration/index.md) |
| Run | Setup, запуск и operational run scenarios. | [`index.md`](./run/index.md) |
| Contracts | JSON schemas для API, config и persisted state. | [`index.md`](./contracts/index.md) |
| Testing | Test map, traceability conventions и suite pages. | [`index.md`](./testing/index.md) |
| ADR | Долгоживущие architecture decisions. | [`index.md`](./adr/index.md) |
| Terms | Каноническая терминология проекта. | [`index.md`](./terms/index.md) |

## Быстрые маршруты чтения

### Понять систему сверху

1. [`vision.md`](./vision.md)
2. [`index.md`](./architecture/index.md)
3. [`system-overview.md`](./architecture/system-overview.md)
4. [`container-view.md`](./architecture/container-view.md)

### Понять service topology

1. [`index.md`](./services/index.md)
2. [`system-overview.md`](./architecture/system-overview.md)
3. [`container-view.md`](./architecture/container-view.md)

### Понять backend runtime boundaries

1. [`container-view.md`](./architecture/container-view.md)
2. [`component-view.md`](./architecture/component-view.md)
3. [`component-map.md`](./architecture/component-map.md)
4. [`runtime-flows.md`](./architecture/runtime-flows.md)

### Понять provider-specific behavior

1. [`index.md`](./providers/index.md)
2. [`openai-chatgpt.md`](./providers/openai-chatgpt.md)
3. [`provider-accounts-config.md`](./configuration/provider-accounts-config.md)

### Поднять систему локально

1. [`setup.md`](./setup.md)
2. [`index.md`](./run/index.md)
3. [`auth.md`](./auth.md)

### Проверить contracts и evidence

1. [`index.md`](./contracts/index.md)
2. [`index.md`](./testing/index.md)
3. [`traceability-map.md`](./architecture/traceability-map.md)
4. [`index.md`](./adr/index.md)

## Related documents

- project vision: [`vision.md`](./vision.md)
- architecture entry point: [`index.md`](./architecture/index.md)
- service map: [`index.md`](./services/index.md)

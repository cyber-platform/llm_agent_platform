# Architecture Index

## Назначение

Этот индекс является главной точкой входа в архитектуру `llm_agent_platform`.

Документация организована по двум осям:

- zoom-level: от high-level устройства системы к package-level реализации и runtime flows;
- structural view: слои, компоненты, контракты, тестовое evidence и ADR.

## Быстрые маршруты

### Понять систему сверху

- Product vision: [`docs/vision.md`](docs/vision.md:1)
- System overview: [`docs/architecture/system-overview.md`](docs/architecture/system-overview.md:1)
- Container view: [`docs/architecture/container-view.md`](docs/architecture/container-view.md:1)
- Web UI: [`docs/architecture/web-ui.md`](docs/architecture/web-ui.md:1)

### Понять слои и правила зависимостей

- Layers: [`docs/architecture/layers.md`](docs/architecture/layers.md:1)
- RBAC: [`docs/architecture/rbac.md`](docs/architecture/rbac.md:1)
- RBAC Roles: [`docs/architecture/rbac-roles.md`](docs/architecture/rbac-roles.md:1)

### Понять терминологию

- Terms Index: [`docs/terms/index.md`](docs/terms/index.md:1)
- Project Terms: [`docs/terms/project/terms-map.md`](docs/terms/project/terms-map.md:1)

### Найти компонент и связанный Python package

- Component map: [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
- Package map: [`docs/architecture/package-map.md`](docs/architecture/package-map.md:1)

### Понять основные runtime interactions

- Runtime flows: [`docs/architecture/runtime-flows.md`](docs/architecture/runtime-flows.md:1)
- OpenAI chat completions pipeline: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
- Quota rotation and groups: [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)

### Понять трассируемость изменений

- Traceability map: [`docs/architecture/traceability-map.md`](docs/architecture/traceability-map.md:1)
- Contracts: [`docs/contracts/`](docs/contracts:1)
- Test map: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- ADRs: [`docs/adr/`](docs/adr:1)

## Как использовать этот набор документов

Для planning новой функциональности рекомендуемый путь такой:

1. Начать с [`docs/architecture/system-overview.md`](docs/architecture/system-overview.md:1), чтобы восстановить high-level picture.
2. Перейти в [`docs/architecture/layers.md`](docs/architecture/layers.md:1), чтобы понять слой и допустимые зависимости.
3. Перейти в [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1), чтобы найти owning component.
4. Перейти в [`docs/architecture/package-map.md`](docs/architecture/package-map.md:1), чтобы найти конкретные Python packages и key modules.
5. Проверить relevant runtime path в [`docs/architecture/runtime-flows.md`](docs/architecture/runtime-flows.md:1).
6. Проверить contracts, provider pages и tests через [`docs/architecture/traceability-map.md`](docs/architecture/traceability-map.md:1).

## Related documents

- Provider matrix: [`docs/providers/README.md`](docs/providers/README.md:1)
- Auth overview: [`docs/auth.md`](docs/auth.md:1)
- Env and runtime layout: [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)

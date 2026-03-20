# План выполнения Task 026: provider contracts и catalog foundation

Status: Approved for architect stage
Связанная задача: [`tasks_descriptions/tasks/026-provider-contracts-and-catalog-foundation.md`](tasks_descriptions/tasks/026-provider-contracts-and-catalog-foundation.md:1)
Связанная спецификация: [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:1)
Связанный outline: [`plans/2026-03-19-provider-centric-contracts-outline.md`](plans/2026-03-19-provider-centric-contracts-outline.md:1)
Связанный ADR: [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1)

## Scope

Task 026 ограничена подготовкой contract-first артефактов и архитектурным выравниванием.

В scope входит:
- JSON schema definitions для provider contracts в [`docs/contracts/`](docs/contracts)
- canonical rules для provider identity
- решение по storage layout для `catalog snapshot`
- decomposition для следующего этапа реализации в [code](llm_agent_platform/__init__.py:1) режиме

Вне scope Task 026:
- реализация runtime registry loader
- route refactor
- runtime behavior для `catalog service`
- provider discovery implementation для `openai-chatgpt`

## Approved decisions

### D-001 Canonical provider identifiers
`provider_id` и `route_name` должны совпадать и использовать kebab-case.

Canonical set:
- `gemini-cli`
- `google-vertex`
- `qwen-code`
- `openai-chatgpt`

Source of truth:
- [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:113)
- [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:32)

### D-002 Contract set for implementation
На следующем шаге реализации должны быть созданы ровно следующие schema files:
- [`docs/contracts/config/provider-descriptor.schema.json`](docs/contracts/config/provider-descriptor.schema.json)
- [`docs/contracts/config/provider-registry.schema.json`](docs/contracts/config/provider-registry.schema.json)
- [`docs/contracts/state/provider-catalog-snapshot.schema.json`](docs/contracts/state/provider-catalog-snapshot.schema.json)

### D-003 Boundary between config contracts and runtime abstractions
- `provider descriptor` — это declarative configuration contract
- `provider registry` — это contract для набора descriptors и правил уникальности
- `runtime adapter` остается отдельной runtime abstraction и не должен смешиваться с descriptor schema

Эта граница соответствует [`plans/2026-03-19-provider-centric-contracts-outline.md`](plans/2026-03-19-provider-centric-contracts-outline.md:50).

### D-004 Snapshot storage layout
`catalog snapshot` сохраняется только для discovery-capable providers.

Approved path:
- `<STATE_DIR>/<provider_id>/catalog/models.json`

Static providers не создают snapshot files и продолжают использовать только `bootstrap catalog`.

Source of truth:
- [`plans/2026-03-19-provider-centric-contracts-outline.md`](plans/2026-03-19-provider-centric-contracts-outline.md:156)
- [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:76)

## Contract intent

### Provider descriptor
Должен определять:
- provider identity
- display metadata
- auth profile
- transport profile
- bootstrap catalog
- optional discovery policy
- catalog cache policy

### Provider registry
Должен определять:
- registry version
- provider collection
- uniqueness constraints для `provider_id` и `route_name`

`provider registry` не должен хранить group definitions, потому что groups остаются в runtime и account-config scope согласно [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:49).

### Provider catalog snapshot
Должен определять:
- `provider_id`
- schema `version`
- `as_of`
- `source`
- `models[]`

`provider catalog snapshot` относится к state-layer data и должен лежать в [`docs/contracts/state/`](docs/contracts/state).

## Handoff в code stage

Последовательность реализации для следующего шага в [code](llm_agent_platform/__init__.py:1) режиме:
1. Создать три schema files в [`docs/contracts/config/`](docs/contracts/config) и [`docs/contracts/state/`](docs/contracts/state)
2. Переиспользовать или согласовать nested model shape для `provider model descriptor` между descriptor и snapshot
3. Сохранить naming consistency с [`docs/contracts/config/provider-accounts-config.schema.json`](docs/contracts/config/provider-accounts-config.schema.json:1) и [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1)
4. Обновить `Execution Status` в [`tasks_descriptions/tasks/026-provider-contracts-and-catalog-foundation.md`](tasks_descriptions/tasks/026-provider-contracts-and-catalog-foundation.md:1) после создания schema files
5. Если во время реализации изменятся schema naming или storage layout, синхронизировать связанные docs и ADR references до закрытия задачи

## Traceability expectations

- Architecture reference: [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1)
- Specification reference: [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:222)
- Test traceability anchor: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Out of scope follow-up tasks

- runtime registry и provider resolution относятся к [`tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md`](tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md:1)
- suite updates и automated coverage updates относятся к [`tasks_descriptions/tasks/028-provider-centric-tests-and-catalog-suite.md`](tasks_descriptions/tasks/028-provider-centric-tests-and-catalog-suite.md:1)
- documentation rebranding относится к [`tasks_descriptions/tasks/029-provider-centric-docs-and-rebranding.md`](tasks_descriptions/tasks/029-provider-centric-docs-and-rebranding.md:1)

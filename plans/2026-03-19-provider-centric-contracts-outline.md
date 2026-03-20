# Provider-centric contracts outline

Status: Proposed
Related spec: [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:1)
Related ADR: [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1)

## Цель

Зафиксировать contract-first артефакты, которые понадобятся для реализации provider-centric платформы без hardcode catalogs в runtime routes.

## 1. Contract set

### C-001 Provider descriptor
Путь:
- `docs/contracts/config/provider-descriptor.schema.json`

Назначение:
- описывает один provider как каноническую конфигурационную сущность.

Важно:
- это не runtime adapter и не порт;
- это декларативный descriptor, который конфигурирует поведение orchestration layer.

Минимальные поля:
- `provider_id`
- `display_name`
- `route_name`
- `auth`
- `transport`
- `catalog`

Ключевые секции:
- `auth.kind`
- `auth.requirements`
- `transport.kind`
- `transport.runtime_adapter`
- `catalog.bootstrap`
- `catalog.discovery`
- `catalog.cache`

Замечание:
- `provider_id` и `route_name` должны совпадать и использовать kebab-case.

В текущем redesign набор provider ids включает:
- `gemini-cli`
- `google-vertex`
- `qwen-code`
- `openai-chatgpt`

Архитектурное различие:
- `provider descriptor` — декларативный контракт конфигурации;
- `provider adapter` — конкретная runtime реализация для данного provider;
- общий порт в гексагональной архитектуре — это интерфейс runtime adapter, например `ProviderAdapter`;
- descriptor не заменяет adapter, а только указывает, какой adapter и какие metadata должны использоваться.

### C-002 Provider registry
Путь:
- `docs/contracts/config/provider-registry.schema.json`

Назначение:
- описывает набор зарегистрированных providers.

Минимальные поля:
- `version`
- `providers[]`

Требования:
- `provider_id` уникален;
- `route_name` уникален;
- registry не содержит групп, потому что groups живут в account config и runtime logic.

### C-003 Provider catalog snapshot
Путь:
- `docs/contracts/state/provider-catalog-snapshot.schema.json`

Назначение:
- описывает локальный сохраненный snapshot каталога моделей конкретного provider.

Ограничение:
- используется только для providers с `discovery refresh`.

Минимальные поля:
- `provider_id`
- `version`
- `as_of`
- `source`
- `models[]`

Пояснение:
- `as_of` — время, когда snapshot был собран и записан локально;
- `source` — `bootstrap` или `discovery`.

### C-004 Provider model descriptor
Можно выделить как отдельную вложенную сущность внутри `provider catalog snapshot` и `provider descriptor`.

Минимальные поля:
- `model_id`
- `display_name`
- `capabilities`
- `lifecycle`
- `upstream_id`
- optional `metadata`

Правила:
- `model_id` должен быть истинным upstream id или согласованным canonical id без suffix-семантики `quota` и `vertex`.
- один и тот же `model_id` может существовать у нескольких providers.

## 2. Границы ответственности

### Provider descriptor отвечает за
- идентичность provider;
- auth profile;
- transport profile;
- bootstrap catalog;
- discovery refresh strategy;
- cache policy.

### Provider registry отвечает за
- список доступных providers;
- загрузку provider descriptor по `provider_id`;
- валидацию уникальности provider ids.

### Catalog snapshot отвечает за
- локально доступный и стабильный источник списка моделей для `GET /models`;
- последнюю валидную materialized версию discovery результата.

## 3. Runtime integration points

### Route layer
Использует provider registry для резолва provider по URL.

### Pipeline layer
Получает `provider_id` из URL и больше не выводит provider по `model id`.

### Catalog service
Реализует lifecycle:
1. load bootstrap
2. load snapshot
3. try discovery refresh
4. validate
5. persist snapshot
6. return provider-local catalog

### Provider adapters
Остаются местом для provider-specific runtime behavior.

Роль в архитектуре:
- `ProviderAdapter` это порт уровня runtime orchestration;
- `GeminiCliAdapter`, `GoogleVertexAdapter`, `QwenCodeAdapter` и будущие адаптеры — его реализации;
- `provider descriptor` — не интерфейс, а входные данные для выбора и настройки нужной реализации.

Важно:
- добавление нового provider без route-code changes возможно только при условии, что существует runtime adapter или generic adapter для его transport profile.
- То есть новый provider descriptor сам по себе не отменяет необходимость provider-specific runtime code, если transport или auth нетиповые.

## 4. Snapshot storage draft

Рекомендованный путь:
- `<STATE_DIR>/<provider_id>/catalog/models.json`

Причины:
- snapshot относится к provider runtime state;
- `STATE_DIR` уже используется как единая зона локального persisted state;
- storage layout остается provider-local и предсказуемым.

Ограничение:
- static providers этот файл не создают;
- для static providers источником истины остается `bootstrap catalog`.

## 5. Open implementation notes

- Для static providers `bootstrap catalog` и persisted snapshot могут долго совпадать.
- Для static providers persisted snapshot не создается.
- Для discoverable providers persisted snapshot становится основной runtime копией каталога.
- Первый discovery-capable provider текущего этапа: `openai-chatgpt`.
- При невалидном discovery payload snapshot не обновляется.
- Запись snapshot должна быть атомарной по тем же принципам надежности, что и другой persisted state.

## 6. Review checklist

- Есть ли единый канонический `provider_id` без dual naming.
- Нет ли suffix-based semantics в `model_id`.
- Есть ли явная граница между config contracts и runtime adapters.
- Достаточно ли полей в snapshot для audit и troubleshooting.
- Не дублируется ли provider data между registry и descriptor.

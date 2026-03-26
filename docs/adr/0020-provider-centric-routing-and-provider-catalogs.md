# ADR 0020: provider-centric routing и provider-local catalogs для LLM Agent Platform

- Status: Proposed
- Date: 2026-03-19

## Контекст

Текущая платформа унаследовала старый proxy-first дизайн:
- provider иногда выводится по имени модели;
- публичные маршруты используют глобальный `group_id` через `/<group_id>/v1/*`;
- часть списков моделей захардкожена в route layer;
- suffix-подход `quota` и `vertex` кодирует transport и billing semantics в model id;
- верхнеуровневая документация местами все еще описывает продукт как Gemini proxy.

Это создает системные проблемы:
- одинаковые `group_id` у разных providers конфликтуют концептуально;
- одинаковые model ids у разных providers нельзя выразить естественно;
- route contract не совпадает с фактической domain model, где state уже изолируется по provider и group;
- добавление provider и catalog logic размазано между route code, mapping code и docs.

## Решение

### 1. Provider становится центральной сущностью публичного API
Каноническими считаются только provider-scoped маршруты:
- `GET /<provider_name>/v1/models`
- `POST /<provider_name>/v1/chat/completions`
- `GET /<provider_name>/<group_name>/v1/models`
- `POST /<provider_name>/<group_name>/v1/chat/completions`

Backward compatibility для старых путей `/v1/*` и `/<group_id>/v1/*` не сохраняется.

### 2. Provider ids единообразны и используют kebab-case
Публичные и внутренние domain ids совпадают:
- `gemini-cli`
- `google-vertex`
- `qwen-code`
- `openai-chatgpt`

### 3. Истинные model ids без suffix-семантики
Публичные model ids должны совпадать с upstream model ids и не содержать suffix вроде `quota` или `vertex`.

Примеры допустимых ids:
- `gemini-3-flash`
- `gemini-2.5-pro`
- `coder-model`

Transport, auth, quota и billing semantics живут в metadata provider, а не в model id.

### 4. Groups — capability платформы
Groups реализуются нашей платформой и существуют только внутри provider namespace.

Следствия:
- одинаковые `group_name` у разных providers допустимы;
- `default group` адресуется через `/<provider_name>/v1/*`;
- если группы объявлены, `default group` определяется как первая группа в provider config;
- если группы не объявлены, `default group` использует все аккаунты provider;
- named group адресуется через `/<provider_name>/<group_name>/v1/*`;
- отдельный provider flag для поддержки groups не нужен.

### 5. Provider-local catalog strategy
Для каждого provider вводится provider-local источник каталога моделей.

Базовый и текущий канонический вариант:
- `bootstrap catalog` — статический локальный набор моделей в provider descriptor.

Допустимое расширение платформы в будущем:
- `persisted catalog snapshot` — локально сохраненный каталог для provider, если для него когда-либо будет принят discovery-based lifecycle;
- `discovery refresh` — optional механизм обновления snapshot, который требует отдельного подтвержденного upstream source и отдельной архитектурной фиксации.

Текущая реализация и канон для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1):
- provider использует static catalog baseline;
- live discovery отсутствует;
- список моделей задается через bootstrap catalog в descriptor.

Порядок резолва каталога в текущем каноне:
1. взять `bootstrap catalog` как локальный каталог provider;
2. вернуть его как Source of Truth для `/models` данного provider.

### 6. Хранение catalog snapshot
`provider catalog snapshot` не является частью текущего канона для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1).

Если в будущем для отдельного provider будет утвержден discovery-based lifecycle, snapshot должен храниться в `STATE_DIR` рядом с другим runtime state.

Поле `as_of` в snapshot в таком случае означает момент, когда локальный snapshot был сформирован и записан, а не дату выпуска модели или обновления upstream каталога.

### 7. Product repositioning
Платформа позиционируется как LLM Agent Platform, а не Gemini proxy.

Документация и narrative должны быть обновлены:
- убрать Gemini-only framing как core definition продукта;
- убрать legacy proxy-first vocabulary там, где речь идет о платформе в целом;
- описывать providers как независимые интеграции внутри общей LLM platform.

## Вне scope текущего ADR
- Native Gemini endpoints как отдельный публичный namespace
- Автоматическая миграция старых клиентских конфигов

## Рассмотренные альтернативы

### Option A: Сохранить выбор provider по model id
- Плюсы: меньше изменений в routes.
- Минусы: не решает коллизии одинаковых model ids и не соответствует новой domain model.

### Option B: Оставить глобальные groups
- Плюсы: короткие URL.
- Минусы: конфликт namespacing между providers и несогласованность с provider-local state.

### Option C: Provider-centric routing и provider-local catalogs
- Плюсы: явный namespace, естественная поддержка одинаковых model ids, отказ от hardcoded route catalogs, согласованность с domain model.
- Минусы: крупный breaking redesign и пересборка route contract, tests и docs.

## Последствия

### Положительные
- Provider становится явной частью HTTP контракта.
- Один и тот же model id может безопасно существовать у нескольких providers.
- Route layer больше не обязан хранить hardcoded catalogs.
- Provider catalog остается детерминированным и provider-local.
- Groups становятся предсказуемой platform capability.

### Негативные и риски
- Нужен coordinated breaking change по routes, pipeline, tests и docs.
- Нужно убрать старую suffix-based model semantics из runtime кода.
- Нужно спроектировать provider descriptor и snapshot contracts.

## Contract changes

- present
- Удаляются legacy public routes `/v1/*` и `/<group_id>/v1/*`.
- Добавляются только provider-scoped public routes `/<provider_name>/v1/*` и `/<provider_name>/<group_name>/v1/*`.
- Публичные `model ids` перестают нести suffix-семантику `quota` и `vertex`.
- Вводится provider-local catalog strategy с bootstrap catalog как текущим каноном и optional future extension для snapshot/discovery.

## Review conditions

- Пересмотреть ADR, если появится обязательная потребность вернуть глобальный `/v1/*` namespace.
- Пересмотреть ADR, если хотя бы один runtime provider не может быть корректно выражен через provider-scoped routing.
- Пересмотреть ADR, если для отдельного provider будет подтвержден и принят discovery-based lifecycle.

## Связанные артефакты
- Product vision: [`docs/vision.md`](docs/vision.md:1)
- Component map: [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
- Provider page: [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- Test traceability: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- Existing ADR: [`docs/adr/0017-url-prefix-groups-and-group-aware-models.md`](docs/adr/0017-url-prefix-groups-and-group-aware-models.md:1)
- Existing ADR: [`docs/adr/0018-quota-reset-periods-and-account-state.md`](docs/adr/0018-quota-reset-periods-and-account-state.md:1)
- Existing ADR: [`docs/adr/0019-state-dir-unified-account-state-and-async-writer.md`](docs/adr/0019-state-dir-unified-account-state-and-async-writer.md:1)

Актуальные provider-specific границы и runtime status должны поддерживаться в [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1) и связанных suite-страницах из [`docs/testing/`](docs/testing:1).

## Следующие шаги
- Зафиксировать contract-first схему provider descriptor и provider-local catalog strategy.
- Подготовить test design для provider-scoped routes и provider-local model validation.
- Обновить верхнеуровневую документацию под narrative LLM Agent Platform.
- После согласования перевести runtime на provider-centric resolution path.

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

### 5. Provider-local catalog lifecycle
Для каждого provider вводится единый lifecycle каталога моделей:
- `bootstrap catalog` — стартовый локальный набор моделей в provider descriptor;
- `persisted catalog snapshot` — локально сохраненный актуальный каталог provider для discovery-capable providers;
- `discovery refresh` — optional механизм обновления snapshot.

Порядок резолва каталога:
1. взять `bootstrap catalog` как локальный базовый каталог;
2. если provider не поддерживает `discovery refresh`, вернуть `bootstrap catalog`;
3. если provider поддерживает `discovery refresh`, использовать последний `persisted snapshot`, если он есть;
4. попытаться выполнить `discovery refresh`;
5. при успехе провалидировать payload и сохранить новый snapshot;
6. при ошибке discovery вернуть последний валидный snapshot, а если его нет — вернуть `bootstrap catalog`.

Для текущего этапа референсной discovery-capable интеграцией считается `openai-chatgpt`, чтобы `discovery refresh` и `catalog snapshot` были частью не только contracts, но и реального target design.

### 6. Хранение catalog snapshot
`provider catalog snapshot` хранится в `STATE_DIR` рядом с другим runtime state, но только для providers с `discovery refresh`.

Поле `as_of` в snapshot означает момент, когда локальный snapshot был сформирован и записан, а не дату выпуска модели или обновления upstream каталога.

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
- Discovery перестает быть точкой отказа для `/models`, потому что есть локальный snapshot.
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
- Вводится provider-local catalog lifecycle с `bootstrap catalog`, `persisted snapshot` и optional `discovery refresh`.

## Review conditions

- Пересмотреть ADR, если появится обязательная потребность вернуть глобальный `/v1/*` namespace.
- Пересмотреть ADR, если хотя бы один runtime provider не может быть корректно выражен через provider-scoped routing.
- Пересмотреть ADR, если `catalog snapshot` в `STATE_DIR` создаст неприемлемые operational риски или конфликт с lifecycle runtime state.
- Пересмотреть ADR, если discovery-first дизайн не сможет быть реализован на `openai-chatgpt` без нарушения provider-centric контрактов.

## Связанные артефакты
- Spec: [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:1)
- Existing ADR: [`docs/adr/0017-url-prefix-groups-and-group-aware-models.md`](docs/adr/0017-url-prefix-groups-and-group-aware-models.md:1)
- Existing ADR: [`docs/adr/0018-quota-reset-periods-and-account-state.md`](docs/adr/0018-quota-reset-periods-and-account-state.md:1)
- Existing ADR: [`docs/adr/0019-state-dir-unified-account-state-and-async-writer.md`](docs/adr/0019-state-dir-unified-account-state-and-async-writer.md:1)

Связанные риски и открытые вопросы описаны в [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:1).

## Следующие шаги
- Зафиксировать contract-first схему provider descriptor и catalog snapshot.
- Подготовить test design для provider-scoped routes и provider-local model validation.
- Обновить верхнеуровневую документацию под narrative LLM Agent Platform.
- После согласования перевести runtime на provider-centric resolution path.

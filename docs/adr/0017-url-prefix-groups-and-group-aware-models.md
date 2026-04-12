# ADR 0017: URL-prefix quota groups + group-aware `GET /v1/models`

- Status: Superseded by [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1)
- Date: 2026-03-16

## Superseded note

Этот ADR сохраняется только как ранний шаг эволюции quota-групп.

Текущий активный канон больше не использует глобальные маршруты `/v1/*` и `/<group_id>/v1/*` как публичный namespace. Вместо этого платформа использует provider-scoped routing из [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:23):

- `/<provider_name>/v1/*`
- `/<provider_name>/<group_name>/v1/*`

Ниже документ сохраняется только для понимания происхождения идеи provider-local group isolation.

## Контекст

Прокси обслуживает quota-first сценарии через несколько аккаунтов и нуждается в:

1) **изоляции state** (счётчики ошибок/успехов, cooldown/exhausted, указатель текущего аккаунта) между разными «агентами/клиентами»;
2) **group-aware списка моделей** (разные группы могут иметь разные разрешённые модели);
3) способа выбирать группу, который совместим с OpenAI-compatible клиентами.

Ограничение: многие OpenAI-compatible клиенты не поддерживают (или сложно конфигурируются на) кастомные headers для каждого запроса, но поддерживают настройку `base_url`.

## Решение

### 1) Group selection: URL-prefix (вариант B)

Использовать group id как часть пути:
- default группа `g0` обслуживается на `/v1/*`;
- произвольная группа обслуживается на `/<group_id>/v1/*`.

Эндпоинты:
- `POST /v1/chat/completions`
- `POST /<group_id>/v1/chat/completions`
- `GET /v1/models`
- `GET /<group_id>/v1/models`

### 2) Group-aware `GET /v1/models`

Если в provider accounts-config задано `groups`, список моделей формируется из `groups.<gid>.models` (union по провайдерам) для соответствующего `group_id`.

Если `groups` отсутствует, применяется backward-compatible поведение: модели определяются динамически по доступным источникам авторизации (см. описание поведения в [`docs/auth.md`](docs/auth.md:134)).

## Обоснование

- URL-prefix меняет только `base_url`, не требует поддержки headers у клиента.
- Группа становится явной частью интерфейса и позволяет гарантировать изоляцию state по ключу `(provider_id, group_id)`.
- `/v1/models` становится согласованным с `base_url` группы: один и тот же клиент, настроенный на `/<group_id>/v1`, получает корректный список моделей.

## Рассмотренные альтернативы

### Option A: отдельный инстанс прокси на группу (порт/контейнер)
- Плюсы: максимальная изоляция (процессы), путь `/v1/*` без префикса.
- Минусы: операционная сложность (несколько сервисов/портов), дублирование конфигурации и наблюдаемости.

### Option B: group id через HTTP header
- Плюсы: не меняет URL.
- Минусы: не подходит из-за ограничения клиентов (header сложно/невозможно задавать стабильно).

### Option C (выбрано): URL-prefix groups
- Плюсы: один инстанс прокси, один порт; совместимо с клиентами через `base_url`.
- Минусы: требует добавления префиксных маршрутов и явной договорённости по `/v1/models`.

## Последствия

### Позитивные
- Изоляция state между группами в одном процессе.
- Явное и предсказуемое поведение `/v1/models` для разных групп.
- Масштабирование групп без увеличения числа контейнеров.

### Негативные / риски
- Клиенты должны уметь настраивать `base_url` с префиксом `/<group_id>/v1`.
- Требуется аккуратная backward compatibility для конфигов без `groups`.

## Связанные канонические документы

- Канон по quota rotation + groups: [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)
- База по 429 policy: [`docs/adr/0014-stream-state-container-and-429-rotation-policy.md`](docs/adr/0014-stream-state-container-and-429-rotation-policy.md:1)

## Contract changes

- present
- `GET /<group_id>/v1/models` и `POST /<group_id>/v1/chat/completions` добавлены как дополнительные маршруты.
- Поведение `/v1/models` расширено: поддержка group-aware списка моделей при наличии `groups`.

## Verification

- Компиляция: `cd services/backend && uv run python -m compileall llm_agent_platform`
- Тесты: `cd services/backend && uv run python -m unittest discover -s llm_agent_platform/tests -p "test_*.py"`
- Трассировка тестов: [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)

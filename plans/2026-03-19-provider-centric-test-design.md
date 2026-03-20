# Provider-centric redesign test design

Status: Proposed
Related spec: [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:1)
Related ADR: [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1)

## Цель

Зафиксировать тестовый контур для breaking change, в котором:
- provider выбирается по URL;
- модель валидируется внутри provider-local catalog;
- глобальные `quota` и `vertex` suffix models исчезают из публичного контракта;
- `GET /models` работает через `bootstrap catalog` или `catalog snapshot` в зависимости от типа provider.

## Scope

### Входит в scope
- provider-scoped OpenAI-compatible routes;
- provider-local groups;
- provider-local catalog validation;
- `catalog snapshot` fallback для discovery-capable providers;
- `openai-chatgpt` как первый discovery-capable provider;
- doc narrative review для ключевых product pages.

### Не входит в scope
- Полный runtime контракт будущих providers вне текущего набора;
- Native provider-specific endpoints вне OpenAI-compatible surface;
- Детальный E2E с реальными upstream credentials.

## Test suites impact

### Suite A: OpenAI contract
Связанный suite:
- [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1)

Нужно дополнить:
- provider-scoped `chat/completions` routes;
- одинаковые `model ids` у разных providers;
- проверку отсутствия suffix-based public ids.

### Suite B: Proxy routes
Связанный suite:
- [`docs/testing/suites/proxy-routes.md`](docs/testing/suites/proxy-routes.md:1)

Нужно дополнить:
- `GET /<provider_name>/v1/models`
- `GET /<provider_name>/<group_name>/v1/models`
- негативные кейсы unknown provider
- негативные кейсы unknown group inside provider

### Suite C: Quota account rotation
Связанный suite:
- [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)

Нужно дополнить:
- provider-local group namespaces вместо глобальных groups;
- state isolation по `provider_id + group_id` при одинаковых group names у разных providers.

### Suite D: Catalog lifecycle
Новый planned suite:
- `docs/testing/suites/provider-catalogs.md`

Назначение:
- покрыть `bootstrap catalog`, `catalog snapshot`, `discovery refresh`, fallback semantics.

## Test cases

### TC-ROUTE-001 Provider default route
Дано `provider-scoped URL` вида `/<provider_name>/v1/chat/completions`
Когда `route parser` разбирает путь
Тогда provider резолвится из URL, а `default group` выбирается неявно как первая группа из config или как все аккаунты provider, если группы не заданы

### TC-ROUTE-002 Provider named group route
Дано `provider-scoped URL` вида `/<provider_name>/<group_name>/v1/chat/completions`
Когда `route parser` разбирает путь
Тогда provider и `named group` резолвятся из URL

### TC-ROUTE-003 Unknown provider
Дано неизвестное значение `provider_name`
Когда клиент вызывает `provider-scoped route`
Тогда сервис возвращает `contract error` с явной диагностикой неизвестного provider

### TC-ROUTE-004 Unknown group inside provider
Дано известное значение provider и неизвестное значение `group_name`
Когда клиент вызывает `provider-group route`
Тогда сервис возвращает `contract error` для неизвестной группы внутри provider namespace

### TC-MODEL-001 Same model id in multiple providers
Дано два providers с одинаковым `model_id`
Когда клиент обращается к одному `provider-specific path`
Тогда валидация использует только `provider-local catalog` выбранного provider

### TC-MODEL-002 Public model ids without suffix
Дано `provider catalog` с публичными model ids
Когда клиент вызывает provider `/models`
Тогда возвращаемые `model ids` не содержат `quota` и `vertex`

### TC-MODEL-003 Static provider catalog
Дано `static provider` без `discovery support`
Когда клиент вызывает provider `/models`
Тогда сервис возвращает модели из `bootstrap catalog` без зависимости от `persisted snapshot`

### TC-MODEL-004 Discovery provider snapshot refresh
Дано `openai-chatgpt` как `discovery-capable provider` и успешный `discovery response`
Когда клиент вызывает provider `/models`
Тогда сервис обновляет локальный `catalog snapshot` и возвращает обновленный каталог моделей

### TC-MODEL-005 Discovery provider fallback
Дано `openai-chatgpt` как `discovery-capable provider` и ошибка в `discovery refresh`
Когда клиент вызывает provider `/models`
Тогда сервис возвращает последний валидный `catalog snapshot`, а при его отсутствии — `bootstrap catalog`

### TC-GROUP-001 Same group name across providers
Дано несколько providers с одинаковым `group_name`
Когда запросы приходят в оба `provider-scoped group routes`
Тогда `state`, `models` и `account pools` остаются изолированными внутри каждого provider namespace

### TC-DOC-001 Product narrative cleanup
Дан обновленный набор `top-level docs`
Когда выполняется `docs review`
Тогда продукт описывается как `LLM Agent Platform`, а не как Gemini proxy

## Coverage mapping

| Requirement | Test case | Level | Target script or suite |
|---|---|---|---|
| US-001 | TC-ROUTE-001 TC-ROUTE-003 | L3 | route tests |
| US-002 | TC-ROUTE-002 TC-GROUP-001 | L3 | route and router tests |
| US-003 | TC-MODEL-001 TC-MODEL-002 | L2 L3 | contract tests |
| US-004 | TC-MODEL-003 | L2 | catalog tests |
| US-005 | TC-MODEL-004 TC-MODEL-005 | L2 L3 | catalog tests |
| US-006 | TC-DOC-001 | L1 | docs review |

## Planned scripts impact

### Update existing
- [`llm_agent_platform/tests/test_refactor_p2_routes.py`](llm_agent_platform/tests/test_refactor_p2_routes.py:1)
- [`llm_agent_platform/tests/test_openai_contract.py`](llm_agent_platform/tests/test_openai_contract.py:1)
- [`llm_agent_platform/tests/test_quota_account_router.py`](llm_agent_platform/tests/test_quota_account_router.py:1)

### Add new
- `llm_agent_platform/tests/test_provider_catalogs.py`

## Verification commands

- `uv run python -m unittest llm_agent_platform/tests/test_refactor_p2_routes.py`
- `uv run python -m unittest llm_agent_platform/tests/test_openai_contract.py`
- `uv run python -m unittest llm_agent_platform/tests/test_quota_account_router.py`
- `uv run python -m unittest llm_agent_platform/tests/test_provider_catalogs.py`
- `uv run python -m unittest discover -s llm_agent_platform/tests -p "test_*.py"`

## Review notes

- Test map нужно будет обновить после реализации.
- Для `catalog snapshot` нужны deterministic fixtures с локальным persisted state.
- Для static providers нужно явно проверить отсутствие попытки читать snapshot как обязательный источник.

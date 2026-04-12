# Видение проекта: provider-centric LLM Agent Platform

## Что это за система

[`README.md`](README.md:1) и архитектурный канон в [`docs/architecture/`](docs/architecture:1) описывают платформу как provider-centric слой доступа для LLM-агентов.

Система предоставляет:
- единый OpenAI-compatible surface для агентных инструментов;
- provider-scoped routing через `/<provider_name>/v1/*` и `/<provider_name>/<group_name>/v1/*`;
- поддержку нескольких провайдеров с одинаковыми `model_id` без конфликта namespace;
- единые правила маршрутизации, авторизации, quota-handling и тестовой трассировки.

## Продуктовая идея

Платформа нужна это общий runtime-слой для LLM-агентов и developer tools.

Ключевая идея:
- provider является центральной сущностью системы;
- модели принадлежат provider-local catalog;
- группы аккаунтов живут внутри provider namespace;
- все LLM доступным по OpenAI совместимому API, он используется как публичный contract.

## Что входит в общий канон

Общие документы должны описывать только устройство платформы и ее сквозные возможности:
- карта компонентов в [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1);
- общий OpenAI pipeline в [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1);
- auth и runtime boundaries в [`docs/auth.md`](docs/auth.md:1) и [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1);
- contracts в [`docs/contracts/`](docs/contracts:1);
- тестовую трассировку в [`docs/testing/index.md`](docs/testing/index.md:1).

Список providers и их актуальный статус должны сводиться в [`docs/providers/index.md`](docs/providers/index.md:1).

## Как документировать провайдеров

Провайдер-специфичные особенности не должны размывать общий канон.

Поэтому для каждого провайдера нужно держать отдельную страницу в [`docs/providers/`](docs/providers:1), где фиксируются:
- auth-механика;
- runtime transport specifics;
- ограничения и инварианты;
- состав каталога моделей;
- особенности usage-limits и retry semantics.

Поверх provider pages должен существовать единый индекс свойств providers в [`docs/providers/index.md`](docs/providers/index.md:1).

Первая такая страница: [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1).

## Границы текущего этапа

Текущий Source of Truth находится в [`docs/`](docs:1). Временные плановые и task-артефакты могут использоваться только как исторический контекст, но не должны быть обязательными для понимания актуальной архитектуры.

Для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) в текущем каноне фиксируется:
- static catalog baseline;
- отсутствие live discovery в текущей архитектуре;
- OAuth-based runtime boundary;
- optional `account_id` в state semantics;
- invariant `one forced refresh retry on auth failure`.

## Дальнейшее развитие

Платформа может расширяться новыми провайдерами, не меняя продуктовую модель:
- общий канон остается provider-centric;
- provider-specific детали добавляются на выделенные страницы в [`docs/providers/`](docs/providers:1);
- boundary contracts и test traceability остаются централизованными в [`docs/contracts/index.md`](docs/contracts/index.md:1) и [`docs/testing/index.md`](docs/testing/index.md:1).

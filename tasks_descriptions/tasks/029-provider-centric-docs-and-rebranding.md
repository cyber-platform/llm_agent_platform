# Task: Provider-centric docs and product rebranding

## Контекст
- Источник: [`docs/vision.md`](docs/vision.md:1)
- Связанные артефакты: [`README.md`](README.md:1), [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:76), [`docs/providers/README.md`](docs/providers/README.md:1), [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1)

## Architecture Context References
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:76)
- [ ] [`docs/architecture/component-map.md`](docs/architecture/component-map.md:33)

## Specification References
- [ ] [`docs/vision.md`](docs/vision.md:1)
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:117)

## Test Design References
- [ ] [`docs/testing/suites/provider-catalogs.md`](docs/testing/suites/provider-catalogs.md:1)
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Workflow References
- [ ] `none`

## Цель
- Обновить верхнеуровневую и архитектурную документацию так, чтобы продукт описывался как provider-centric LLM Agent Platform без legacy narrative про Gemini proxy.

## Шаги реализации
- [x] Обновить [`README.md`](README.md:1) под новую product narrative и provider-centric contract
- [x] Обновить [`docs/vision.md`](docs/vision.md:1), [`docs/usage.md`](docs/usage.md:1), [`docs/auth.md`](docs/auth.md:1)
- [x] Обновить архитектурные документы под provider-scoped routing и catalog lifecycle
- [x] Зафиксировать в docs, что `openai-chatgpt` проектируется как OAuth-based provider, а полный runtime adapter реализуется отдельной задачей [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)
- [x] Обновить test docs и suite links под новый contract
- [x] Удалить или переписать legacy описания `quota` и `vertex` как части публичных model ids

## Definition of Done
- [x] Изменения реализованы по спецификации
- [x] Проверки пройдены
- [x] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Задача по docs/rebranding выполнена: текущий SoT синхронизирован в [`README.md`](README.md:1), [`docs/vision.md`](docs/vision.md:1), [`docs/usage.md`](docs/usage.md:1), [`docs/auth.md`](docs/auth.md:1), [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1), [`docs/providers/README.md`](docs/providers/README.md:1), [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1).
- Next Step: Поддерживать narrative через [`docs/`](docs:1) как единственный SoT без зависимости от временных plans.
- Blockers: none
- Contract Changes: present
- Verification: review ключевых docs в [`docs/`](docs:1) на отсутствие legacy proxy-first narrative и на согласованность с [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1)

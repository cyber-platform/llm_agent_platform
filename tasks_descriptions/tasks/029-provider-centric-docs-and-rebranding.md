# Task: Provider-centric docs and product rebranding

## Контекст
- Источник: [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:364)
- Связанные артефакты: [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:76), [`plans/2026-03-19-provider-centric-test-design.md`](plans/2026-03-19-provider-centric-test-design.md:117), [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1)

## Architecture Context References
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:76)
- [ ] [`docs/architecture/component-map.md`](docs/architecture/component-map.md:33)

## Specification References
- [ ] [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:364)
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:117)

## Test Design References
- [ ] [`plans/2026-03-19-provider-centric-test-design.md`](plans/2026-03-19-provider-centric-test-design.md:117)
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Workflow References
- [ ] `none`

## Цель
- Обновить верхнеуровневую и архитектурную документацию так, чтобы продукт описывался как provider-centric LLM Agent Platform без legacy narrative про Gemini proxy.

## Шаги реализации
- [ ] Обновить [`README.md`](README.md:1) под новую product narrative и provider-centric contract
- [ ] Обновить [`docs/vision.md`](docs/vision.md:1), [`docs/usage.md`](docs/usage.md:1), [`docs/auth.md`](docs/auth.md:1)
- [ ] Обновить архитектурные документы под provider-scoped routing и catalog lifecycle
- [ ] Зафиксировать в docs, что `openai-chatgpt` проектируется как OAuth-based provider, а полный runtime adapter реализуется отдельной задачей [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)
- [ ] Обновить test docs и suite links под новый contract
- [ ] Удалить или переписать legacy описания `quota` и `vertex` как части публичных model ids

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Спецификация и ADR уже зафиксировали новый narrative, но top-level docs и часть architecture docs все еще описывают legacy proxy-first подход
- Next Step: Обновить [`README.md`](README.md:1) и [`docs/usage.md`](docs/usage.md:1) как самые видимые пользовательские точки входа
- Blockers: желательно выполнять после [`tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md`](tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md:1) и [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1), чтобы docs совпадали с фактическим contract и agreed foundation boundary
- Contract Changes: present
- Verification: grep review ключевых docs на legacy narrative по спецификации из [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:378)

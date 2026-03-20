# Task: Provider-centric routing and openai-chatgpt provider

## Контекст
- Источник: [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:124)
- Связанные артефакты: [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:23), [`plans/2026-03-19-provider-centric-contracts-outline.md`](plans/2026-03-19-provider-centric-contracts-outline.md:121)

## Architecture Context References
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:32)
- [ ] [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:34)

## Specification References
- [ ] [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:131)
- [ ] [`plans/2026-03-19-provider-centric-contracts-outline.md`](plans/2026-03-19-provider-centric-contracts-outline.md:123)

## Test Design References
- [ ] [`plans/2026-03-19-provider-centric-test-design.md`](plans/2026-03-19-provider-centric-test-design.md:65)
- [ ] [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1)

## Workflow References
- [ ] `none`

## Цель
- Перевести runtime на provider-centric routing, убрать provider inference по `model id`, реализовать `default group` semantics и добавить `openai-chatgpt` как первый discovery-capable provider.

## Шаги реализации
- [ ] Переделать route parsing на `/<provider_name>/v1/*` и `/<provider_name>/<group_name>/v1/*`
- [ ] Удалить публичную поддержку legacy путей `/v1/*` и `/<group_id>/v1/*`
- [ ] Перевести pipeline на выбор provider из URL вместо `model-name` эвристик
- [ ] Реализовать `default group` как первую группу из config или все аккаунты provider, если группы не заданы
- [ ] Добавить provider adapter и catalog discovery path для `openai-chatgpt`
- [ ] Убрать suffix-based публичные модели `quota` и `vertex` из runtime contract

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Архитектурный target design готов, runtime все еще опирается на legacy routing и model-name inference
- Next Step: Реализовать provider-scoped route contract в [`llm_agent_platform/api/openai/routes.py`](llm_agent_platform/api/openai/routes.py:1) и [`llm_agent_platform/api/openai/pipeline.py`](llm_agent_platform/api/openai/pipeline.py:83)
- Blockers: зависит от выполнения [`tasks_descriptions/tasks/026-provider-contracts-and-catalog-foundation.md`](tasks_descriptions/tasks/026-provider-contracts-and-catalog-foundation.md:1)
- Contract Changes: present
- Verification: `uv run python -m unittest llm_agent_platform/tests/test_refactor_p2_routes.py`


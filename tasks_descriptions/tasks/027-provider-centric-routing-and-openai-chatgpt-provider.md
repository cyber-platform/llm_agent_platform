# Task: Provider-centric routing and provider resolution foundation

## Контекст
- Источник: [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:124)
- Связанные артефакты: [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:23), [`plans/2026-03-19-provider-centric-contracts-outline.md`](plans/2026-03-19-provider-centric-contracts-outline.md:121), [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1), [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)

## Architecture Context References
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:32)
- [ ] [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:34)

## Specification References
- [ ] [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:131)
- [ ] [`plans/2026-03-19-provider-centric-contracts-outline.md`](plans/2026-03-19-provider-centric-contracts-outline.md:123)

## Test Design References
- [ ] [`plans/2026-03-19-provider-centric-test-design.md`](plans/2026-03-19-provider-centric-test-design.md:65)
- [ ] [`docs/testing/suites/proxy-routes.md`](docs/testing/suites/proxy-routes.md:1)

## Workflow References
- [ ] `none`

## Цель
- Перевести runtime на provider-centric routing и provider resolution foundation: убрать provider inference по `model id`, реализовать `default group` semantics и сделать URL единственным входом в provider namespace.

## Шаги реализации
- [ ] Переделать route parsing на `/<provider_name>/v1/*` и `/<provider_name>/<group_name>/v1/*`
- [ ] Удалить публичную поддержку legacy путей `/v1/*` и `/<group_id>/v1/*`
- [ ] Перевести pipeline на выбор provider из URL вместо `model-name` эвристик
- [ ] Реализовать `default group` как первую группу из config или все аккаунты provider, если группы не заданы
- [ ] Перевести route layer на чтение provider registry вместо route hardcode и suffix-driven глобальных списков моделей
- [ ] Убрать suffix-based публичные модели `quota` и `vertex` из runtime contract

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Contract foundation уже готов в [`tasks_descriptions/tasks/026-provider-contracts-and-catalog-foundation.md`](tasks_descriptions/tasks/026-provider-contracts-and-catalog-foundation.md:1), но runtime все еще опирается на legacy routing и model-name inference
- Next Step: Реализовать provider-scoped route contract в [`llm_agent_platform/api/openai/routes.py`](llm_agent_platform/api/openai/routes.py:1) и [`llm_agent_platform/api/openai/pipeline.py`](llm_agent_platform/api/openai/pipeline.py:83)
- Blockers: зависит от выполнения [`tasks_descriptions/tasks/026-provider-contracts-and-catalog-foundation.md`](tasks_descriptions/tasks/026-provider-contracts-and-catalog-foundation.md:1); catalog discovery foundation и auth/state contracts для `openai-chatgpt` вынесены в [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1)
- Contract Changes: present
- Verification: `uv run python -m unittest llm_agent_platform/tests/test_refactor_p2_routes.py`

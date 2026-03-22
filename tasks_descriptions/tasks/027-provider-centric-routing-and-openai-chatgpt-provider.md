# Task: Provider-centric routing and provider resolution foundation

## Контекст
- Источник: [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:23)
- Связанные артефакты: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:34), [`docs/providers/README.md`](docs/providers/README.md:1), [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1), [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)

## Architecture Context References
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:32)
- [ ] [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:34)

## Specification References
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:23)
- [ ] [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:40)

## Test Design References
- [ ] [`docs/testing/suites/proxy-routes.md`](docs/testing/suites/proxy-routes.md:1)
- [ ] [`docs/testing/suites/proxy-routes.md`](docs/testing/suites/proxy-routes.md:1)

## Workflow References
- [ ] `none`

## Цель
- Перевести runtime на provider-centric routing и provider resolution foundation: убрать provider inference по `model id`, реализовать `default group` semantics и сделать URL единственным входом в provider namespace.

## Шаги реализации
- [x] Переделать route parsing на `/<provider_name>/v1/*` и `/<provider_name>/<group_name>/v1/*`
- [x] Удалить публичную поддержку legacy путей `/v1/*` и `/<group_id>/v1/*`
- [x] Перевести pipeline на выбор provider из URL вместо `model-name` эвристик
- [x] Реализовать `default group` как первую группу из config или все аккаунты provider, если группы не заданы
- [x] Перевести route layer на чтение provider registry вместо route hardcode и suffix-driven глобальных списков моделей
- [x] Убрать suffix-based публичные модели `quota` и `vertex` из runtime contract

## Definition of Done
- [x] Изменения реализованы по спецификации
- [x] Проверки пройдены
- [x] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Provider-scoped OpenAI-compatible routing реализован в [`llm_agent_platform/api/openai/routes.py`](llm_agent_platform/api/openai/routes.py:19) и [`llm_agent_platform/api/openai/pipeline.py`](llm_agent_platform/api/openai/pipeline.py:166); runtime больше не использует legacy `/v1/*` и `/<group_id>/v1/*` для OpenAI surface и не выводит provider по `model id` suffix/эвристикам.
- Next Step: Перейти к [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1) для discovery/auth-state foundation `openai-chatgpt`.
- Blockers: runtime adapter для [`llm_agent_platform/provider_registry/providers/openai-chatgpt.json`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1) пока намеренно не реализован в рамках task 027; это остается scope следующей foundation-задачи [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1).
- Contract Changes: present
- Verification: `uv run python -m unittest llm_agent_platform/tests/test_refactor_p2_routes.py llm_agent_platform/tests/test_openai_contract.py`; `uv run python -m unittest discover -s llm_agent_platform/tests -p "test_*.py"`

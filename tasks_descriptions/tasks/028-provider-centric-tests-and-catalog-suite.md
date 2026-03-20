# Task: Provider-centric tests and catalog suite

## Контекст
- Источник: [`plans/2026-03-19-provider-centric-test-design.md`](plans/2026-03-19-provider-centric-test-design.md:1)
- Связанные артефакты: [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:276), [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:117), [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1)

## Architecture Context References
- [ ] [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:60)
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:57)

## Specification References
- [ ] [`plans/2026-03-19-provider-centric-test-design.md`](plans/2026-03-19-provider-centric-test-design.md:65)
- [ ] [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:313)

## Test Design References
- [ ] [`plans/2026-03-19-provider-centric-test-design.md`](plans/2026-03-19-provider-centric-test-design.md:29)
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:7)

## Workflow References
- [ ] `none`

## Цель
- Обновить тестовый контур под provider-centric contract, добавить catalog suite и зафиксировать трассировку для discovery-capable provider `openai-chatgpt`.

## Шаги реализации
- [ ] Обновить route tests под provider-scoped endpoints и `default group` semantics
- [ ] Обновить OpenAI contract tests под provider-local model validation и одинаковые `model ids` у разных providers
- [ ] Дополнить router tests кейсами одинаковых `group_name` у разных providers
- [ ] Добавить `llm_agent_platform/tests/test_provider_catalogs.py` для `bootstrap catalog`, `snapshot refresh` и `fallback`
- [ ] Создать suite `docs/testing/suites/provider-catalogs.md` и обновить [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Test design подготовлен, но текущие tests покрывают legacy routing и не содержат catalog suite
- Next Step: Переписать [`llm_agent_platform/tests/test_refactor_p2_routes.py`](llm_agent_platform/tests/test_refactor_p2_routes.py:1) по сценариям из [`plans/2026-03-19-provider-centric-test-design.md`](plans/2026-03-19-provider-centric-test-design.md:67)
- Blockers: зависит от выполнения [`tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md`](tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md:1) и [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1)
- Contract Changes: present
- Verification: `uv run python -m unittest discover -s llm_agent_platform/tests -p "test_*.py"`

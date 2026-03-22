# Task: Provider-centric tests and catalog suite

## Контекст
- Источник: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- Связанные артефакты: [`docs/testing/suites/provider-catalogs.md`](docs/testing/suites/provider-catalogs.md:1), [`docs/providers/README.md`](docs/providers/README.md:1), [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1), [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)

## Architecture Context References
- [ ] [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:60)
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:57)

## Specification References
- [ ] [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1)
- [ ] [`docs/testing/suites/provider-catalogs.md`](docs/testing/suites/provider-catalogs.md:1)

## Test Design References
- [ ] [`docs/testing/suites/proxy-routes.md`](docs/testing/suites/proxy-routes.md:1)
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:7)

## Workflow References
- [ ] `none`

## Цель
- Обновить тестовый контур под provider-centric contract, поддержать catalog suite и зафиксировать трассировку для static catalog baseline [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) и будущих discovery-capable providers как platform capability.

## Шаги реализации
- [x] Обновить route tests под provider-scoped endpoints и `default group` semantics
- [x] Обновить OpenAI contract tests под provider-local model validation и одинаковые `model ids` у разных providers
- [x] Дополнить router tests кейсами одинаковых `group_name` у разных providers
- [x] Поддерживать `llm_agent_platform/tests/test_provider_catalogs.py` как suite для static catalogs и optional future discovery capability
- [x] Создать suite `docs/testing/suites/provider-catalogs.md` и обновить [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Definition of Done
- [x] Изменения реализованы по спецификации
- [x] Проверки пройдены
- [x] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Базовый provider-centric test contour уже существует в [`docs/testing/test-map.md`](docs/testing/test-map.md:1), [`docs/testing/suites/provider-catalogs.md`](docs/testing/suites/provider-catalogs.md:1) и [`llm_agent_platform/tests/test_provider_catalogs.py`](llm_agent_platform/tests/test_provider_catalogs.py:1), но future follow-up может потребоваться для новых providers и расширения catalog capabilities.
- Next Step: Использовать [`docs/providers/README.md`](docs/providers/README.md:1) и [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1) как SoT при добавлении новых provider-specific test cases.
- Blockers: none
- Contract Changes: present
- Verification: `uv run python -m unittest discover -s llm_agent_platform/tests -p "test_*.py"`

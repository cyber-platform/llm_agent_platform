# Task: OpenAI ChatGPT catalog and OAuth foundation

## Контекст
- Источник: [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- Связанные артефакты: [`docs/providers/README.md`](docs/providers/README.md:1), [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:60), [`tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md`](tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md:1), [`tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md:1), [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)

## Architecture Context References
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:60)
- [ ] [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)

## Specification References
- [ ] [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:19)
- [ ] [`docs/contracts/state/openai-chatgpt-oauth-state.schema.json`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:1)

## Test Design References
- [ ] [`docs/testing/suites/provider-catalogs.md`](docs/testing/suites/provider-catalogs.md:1)
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Workflow References
- [ ] `none`

## Цель
- Подготовить foundation для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) как static catalog provider с OAuth state boundary и usage-limits contracts без полной реализации upstream runtime adapter.

## Шаги реализации
- [x] Зафиксировать, что `openai-chatgpt` входит в общий provider-scoped `/models` contract наравне с другими providers
- [x] Зафиксировать static bootstrap catalog как текущий active SoT для `openai-chatgpt`
- [x] Подготовить runtime boundary для `openai-chatgpt` без полноценного chat adapter: provider visibility, state contracts и storage path в `STATE_DIR`
- [x] Спроектировать auth/state contracts для будущего OAuth-провайдера по аналогии с [`scripts/get_qwen-code_credentials.py`](scripts/get_qwen-code_credentials.py:1), включая usage-limits и reset ETA
- [x] Явно определить, какие части runtime будут зависеть от исследования [`tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md:1)
- [x] Синхронизировать task boundary с runtime implementation в [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)

## Definition of Done
- [x] Изменения реализованы по спецификации
- [x] Проверки пройдены
- [x] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Foundation реализован и синхронизирован с текущим SoT: [`llm_agent_platform/provider_registry/providers/openai-chatgpt.json`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1) описывает static bootstrap catalog и OAuth foundation metadata, а contracts для auth/usage state добавлены в [`docs/contracts/state/openai-chatgpt-oauth-state.schema.json`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:1) и [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1). Live discovery не считается частью active architecture для этого provider.
- Next Step: Использовать результаты [`tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md:1) для реализации полноценного OAuth bootstrap/runtime adapter в [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)
- Blockers: runtime adapter `openai_chatgpt` и точная upstream OAuth semantics intentionally вынесены в [`tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md:1) и [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)
- Contract Changes: present
- Verification: `uv run python -m unittest llm_agent_platform/tests/test_provider_catalogs.py && uv run python -m unittest llm_agent_platform/tests/test_refactor_p2_routes.py`

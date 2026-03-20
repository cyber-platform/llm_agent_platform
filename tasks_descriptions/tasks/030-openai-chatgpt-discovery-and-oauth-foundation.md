# Task: OpenAI ChatGPT discovery and OAuth foundation

## Контекст
- Источник: [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:278)
- Связанные артефакты: [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:60), [`tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md`](tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md:1), [`tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md:1), [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)

## Architecture Context References
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:60)
- [ ] [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)

## Specification References
- [ ] [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:278)
- [ ] [`plans/2026-03-19-provider-centric-contracts-outline.md`](plans/2026-03-19-provider-centric-contracts-outline.md:121)

## Test Design References
- [ ] [`plans/2026-03-19-provider-centric-test-design.md`](plans/2026-03-19-provider-centric-test-design.md:103)
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Workflow References
- [ ] `none`

## Цель
- Подготовить foundation для первого discovery-capable provider `openai-chatgpt`: synchronous best-effort discovery на `/models`, snapshot fallback и contract-first контуры для будущего OAuth runtime и usage-limits state без полной реализации upstream adapter.

## Шаги реализации
- [ ] Зафиксировать, что `openai-chatgpt` входит в общий provider-scoped `/models` contract наравне с другими providers
- [ ] Реализовать `catalog lifecycle` для discovery-capable providers: bootstrap -> snapshot -> live discovery -> fallback
- [ ] Подготовить runtime boundary для `openai-chatgpt` без полноценного chat adapter: provider visibility, catalog refresh hook и storage path в `STATE_DIR`
- [ ] Спроектировать auth/state contracts для будущего OAuth-провайдера по аналогии с [`scripts/get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py:1), включая usage-limits и reset ETA
- [ ] Явно определить, какие части runtime будут зависеть от исследования [`tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md:1)
- [ ] Синхронизировать task boundary с runtime implementation в [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: В [`llm_agent_platform/provider_registry/providers/openai-chatgpt.json`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1) уже есть bootstrap descriptor, но discovery lifecycle и OAuth/state boundary пока не выделены в отдельный deliverable
- Next Step: Выделить catalog/discovery foundation и auth-state contracts в отдельный implementation scope до runtime adapter
- Blockers: зависит от базового routing/refactor в [`tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md`](tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md:1); полный runtime adapter intentionally вынесен в [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)
- Contract Changes: present
- Verification: `uv run python -m unittest llm_agent_platform/tests/test_provider_catalogs.py`

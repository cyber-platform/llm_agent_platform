# Task: OpenAI ChatGPT OAuth runtime integration

## Контекст
- Источник: [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1)
- Связанные артефакты: [`tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md`](tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md:1), [`tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md:1), [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:74)

## Architecture Context References
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:74)
- [ ] [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)

## Specification References
- [ ] [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:83)
- [ ] [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1)
- [ ] [`tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md:1)

## Test Design References
- [ ] [`plans/2026-03-19-provider-centric-test-design.md`](plans/2026-03-19-provider-centric-test-design.md:103)
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Workflow References
- [ ] `none`

## Цель
- Реализовать полноценный runtime provider `openai-chatgpt` поверх уже согласованного foundation: OAuth bootstrap, runtime credentials loading, upstream adapter, usage-limits tracking и reset ETA semantics по подтвержденному исследованием референсу из KiloCode.

## Шаги реализации
- [ ] Использовать результаты [`tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md:1) как обязательный input для runtime design
- [ ] Создать OAuth bootstrap script для `openai-chatgpt` по аналогии с [`scripts/get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py:1)
- [ ] Реализовать хранение и чтение runtime credentials для `openai-chatgpt`
- [ ] Добавить upstream provider adapter для `chat/completions` и streaming
- [ ] Интегрировать usage-limits tracking и reset ETA в state layer без смешения с legacy `last_used_at.json` semantics
- [ ] Синхронизировать bootstrap catalog и live discovery с реальным runtime provider behavior

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Зафиксировано решение, что `openai-chatgpt` работает по OAuth-модели, похожей на Qwen, но текущий task содержит только черновые заметки
- Next Step: После завершения foundation из [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1) и исследования [`tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md:1) сформировать конкретный runtime plan для script, adapter и state persistence
- Blockers: зависит от выполнения [`tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md`](tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md:1), [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1) и [`tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md:1)
- Contract Changes: present
- Verification: `uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_runtime.py`

# Task: OpenAI ChatGPT OAuth runtime integration

## Контекст
- Источник: [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1)
- Связанные артефакты: [`tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md`](tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md:1), [`tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md:1), [`tasks_descriptions/research/2026-03-21-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/research/2026-03-21-openai-codex-oauth-and-usage-research.md:1), [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:74), [`docs/contracts/state/openai-chatgpt-oauth-state.schema.json`](docs/contracts/state/openai-chatgpt-oauth-state.schema.json:1), [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1)

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
- Реализовать полноценный runtime provider `openai-chatgpt` поверх уже согласованного foundation, research report [`tasks_descriptions/research/2026-03-21-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/research/2026-03-21-openai-codex-oauth-and-usage-research.md:1) и architect plan [`plans/2026-03-23-task-016-openai-chatgpt-runtime-plan.md`](plans/2026-03-23-task-016-openai-chatgpt-runtime-plan.md:1): OAuth bootstrap, runtime credentials loading, private chat backend adapter, optional `account_id`, static catalog baseline, общий набор provider mechanisms платформы, поддержка `single` и `rounding` режимов по provider config, provider-local groups и weekly-like quota reset periods через `model_quota_resets`.

## Шаги реализации
- [ ] Использовать результаты [`tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/tasks/031-openai-codex-oauth-and-usage-research.md:1) и отчет [`tasks_descriptions/research/2026-03-21-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/research/2026-03-21-openai-codex-oauth-and-usage-research.md:1) как обязательный input для runtime design
- [ ] Создать OAuth bootstrap script для `openai-chatgpt` по аналогии с [`scripts/get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py:1), но с Authorization Code + PKCE flow из reference [`externel_projects/kilocode/src/integrations/openai-codex/oauth.ts`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:1)
- [ ] Реализовать хранение и чтение runtime credentials для `openai-chatgpt` с optional `account_id` и без предположения, что `ChatGPT-Account-Id` доступен всегда
- [ ] Добавить отдельный upstream `ChatRuntimeAdapter` для приватного backend path и обязательных headers из reference [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts:341)
- [ ] Поддержать общий platform baseline для provider: `single` и `rounding` режимы выбираются provider accounts-config, а не hardcoded strategy веткой
- [ ] Подключить `openai-chatgpt` к существующему quota contour [`llm_agent_platform/services/account_router.py`](llm_agent_platform/services/account_router.py:109), включая provider-local groups и group-aware `/models`
- [ ] Зафиксировать `model_quota_resets` как источник quota reset periods для этого provider, включая weekly-like reset `07:00:00` как типовой baseline
- [ ] Зафиксировать auth-failure behavior как `one forced refresh retry`, без бесконечного retry loop
- [ ] Интегрировать `ProviderUsageLimitsPort` и provider-specific adapter для `openai-chatgpt` только как monitoring capability: usage state не участвует в routing и quota decisions
- [ ] Оставить static catalog baseline для `openai-chatgpt`, удалить legacy discovery semantics из descriptor и не включать live discovery в обязательный runtime scope текущей задачи
- [ ] Зафиксировать initial static catalog для descriptor [`llm_agent_platform/provider_registry/providers/openai-chatgpt.json`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1): `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.3-codex`, `gpt-5.2-codex`, `gpt-5.2`, `gpt-5.1-codex-max`, `gpt-5.1-codex-mini`

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Runtime implementation выполнена: descriptor [`llm_agent_platform/provider_registry/providers/openai-chatgpt.json`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1) переведен на static-only catalog baseline, добавлены OAuth bootstrap script [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py:1) и auth manager [`llm_agent_platform/auth/openai_chatgpt_oauth.py`](llm_agent_platform/auth/openai_chatgpt_oauth.py:1), private backend adapter [`llm_agent_platform/api/openai/providers/openai_chatgpt.py`](llm_agent_platform/api/openai/providers/openai_chatgpt.py:1), provider usage port [`llm_agent_platform/services/provider_usage_limits.py`](llm_agent_platform/services/provider_usage_limits.py:1), а также config/router wiring для `single|rounding` и provider-local groups.
- Next Step: Прогнать полный тестовый контур, затем синхронизировать Memory Bank под фактическую реализацию task 016.
- Blockers: осталось только финальное подтверждение полным набором тестов и обновление Memory Bank; исследовательская и foundation-зависимости уже закрыты артефактами [`tasks_descriptions/research/2026-03-21-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/research/2026-03-21-openai-codex-oauth-and-usage-research.md:1) и [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1)
- Contract Changes: present
- Verification: `uv run python -m unittest llm_agent_platform/tests/test_provider_catalogs.py llm_agent_platform/tests/test_openai_chatgpt_runtime.py`

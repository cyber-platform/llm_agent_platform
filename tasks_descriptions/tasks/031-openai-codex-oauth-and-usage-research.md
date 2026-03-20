# Task: Research OpenAI Codex OAuth and usage-limits in KiloCode

## Контекст
- Источник: [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)
- Связанные артефакты: [`externel_projects/kilocode/src/integrations/openai-codex/oauth.ts`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:1), [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts:1), [`externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:1), [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1)

## Architecture Context References
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:74)
- [ ] [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)

## Specification References
- [ ] [`plans/2026-03-19-provider-centric-platform-redesign-spec.md`](plans/2026-03-19-provider-centric-platform-redesign-spec.md:83)
- [ ] [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1)

## Test Design References
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- [ ] [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)

## Workflow References
- [ ] `none`

## Цель
- Исследовать реализацию OAuth, request flow, account-id propagation и usage-limits/reset ETA для `openai-codex` в [`externel_projects/kilocode`](externel_projects/kilocode), чтобы runtime integration в [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1) опиралась на проверенный референс, а не на догадки.

## Шаги реализации
- [ ] Разобрать OAuth flow в [`externel_projects/kilocode/src/integrations/openai-codex/oauth.ts`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:1): endpoints, PKCE, callback, scopes, token refresh и storage semantics
- [ ] Разобрать runtime request path в [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts:1): backend URL, required headers, account-id propagation, retry-on-auth-failure и model subset
- [ ] Разобрать usage-limits flow в [`externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:1): WHAM endpoint, payload shape, percent semantics и reset timestamps
- [ ] Сопоставить найденное с нашими contracts и выделить, что можно заимствовать буквально, а что требует адаптации под provider-centric runtime
- [ ] Зафиксировать выводы как input для runtime implementation в [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)

## Definition of Done
- [ ] Исследование завершено и выводы задокументированы
- [ ] Явно зафиксированы переносимые и непереносимые части реализации
- [ ] [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1) обновлена ссылками на результаты исследования

## Execution Status
- Current State: Найдены ключевые референсы в [`externel_projects/kilocode/src/integrations/openai-codex/oauth.ts`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:1), [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts:1), [`externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:1), но они еще не синтезированы в отдельный исследовательский deliverable
- Next Step: Подготовить исследовательскую выжимку по OAuth, headers и usage-limits semantics перед runtime design
- Blockers: none
- Contract Changes: none
- Verification: review memo со ссылками на конкретные места в [`externel_projects/kilocode/src/integrations/openai-codex/oauth.ts`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:1), [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts:1), [`externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:1)

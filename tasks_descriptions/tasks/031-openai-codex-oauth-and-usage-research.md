# Task: Research OpenAI Codex OAuth and usage-limits in KiloCode

## Контекст
- Источник: [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)
- Связанные артефакты: [`externel_projects/kilocode/src/integrations/openai-codex/oauth.ts`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:1), [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts:1), [`externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:1), [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1)

## Architecture Context References
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:74)
- [ ] [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)

## Specification References
- [ ] [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:31)
- [ ] [`tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md`](tasks_descriptions/tasks/030-openai-chatgpt-discovery-and-oauth-foundation.md:1)

## Test Design References
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- [ ] [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)

## Workflow References
- [ ] `none`

## Цель
- Исследовать реализацию OAuth, request flow, account-id propagation и usage-limits/reset ETA для `openai-codex` в [`externel_projects/kilocode`](externel_projects/kilocode), зафиксировать результаты в исследовательском отчете и использовать их как обязательный вход для runtime integration в [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1).

## Шаги реализации
- [x] Разобрать OAuth flow в [`externel_projects/kilocode/src/integrations/openai-codex/oauth.ts`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:1): endpoints, PKCE, callback, scopes, token refresh и storage semantics
- [x] Разобрать runtime request path в [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts:1): backend URL, required headers, account-id propagation, retry-on-auth-failure и model subset
- [x] Разобрать usage-limits flow в [`externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:1): WHAM endpoint, payload shape, percent semantics и reset timestamps
- [x] Сопоставить найденное с нашими contracts и выделить, что можно заимствовать буквально, а что требует адаптации под provider-centric runtime
- [x] Зафиксировать выводы как input для runtime implementation в [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)

## Definition of Done
- [x] Исследование завершено и выводы задокументированы
- [x] Явно зафиксированы переносимые и непереносимые части реализации
- [x] [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1) обновлена ссылками на результаты исследования

## Execution Status
- Current State: Исследование завершено и синтезировано в [`tasks_descriptions/research/2026-03-21-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/research/2026-03-21-openai-codex-oauth-and-usage-research.md:1). Зафиксированы OAuth reference semantics, runtime headers, usage-limits adapter pattern, optional `account_id` и решение считать `openai-chatgpt` static-catalog provider без обязательного live discovery в текущем scope.
- Next Step: Использовать выводы из [`tasks_descriptions/research/2026-03-21-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/research/2026-03-21-openai-codex-oauth-and-usage-research.md:1) для runtime design и implementation plan в [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1).
- Blockers: none
- Contract Changes: none
- Verification: исследовательский отчет со ссылками на конкретные места в [`externel_projects/kilocode/src/integrations/openai-codex/oauth.ts`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:1), [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts:1), [`externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts:1): [`tasks_descriptions/research/2026-03-21-openai-codex-oauth-and-usage-research.md`](tasks_descriptions/research/2026-03-21-openai-codex-oauth-and-usage-research.md:1)

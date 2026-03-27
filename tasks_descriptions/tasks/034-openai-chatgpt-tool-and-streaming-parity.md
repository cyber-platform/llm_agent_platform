# Task: OpenAI ChatGPT tool-call and streaming parity

## Контекст
- Источник: [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:1)
- Связанные артефакты: [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1), [`llm_agent_platform/api/openai/providers/openai_chatgpt.py`](llm_agent_platform/api/openai/providers/openai_chatgpt.py:1), [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts:1), [`externel_projects/kilocode/src/utils/mcp-name.ts`](externel_projects/kilocode/src/utils/mcp-name.ts:1), [`externel_projects/kilocode/src/utils/tool-id.ts`](externel_projects/kilocode/src/utils/tool-id.ts:1)

## Architecture Context References
- [ ] [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
- [ ] [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:76)

## Specification References
- [ ] [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:22)
- [ ] [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:23)

## Test Design References
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:10)
- [ ] [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1)

## Workflow References
- [ ] `none`

## Цель
- Довести [`openai_chatgpt`](llm_agent_platform/api/openai/providers/openai_chatgpt.py:1) до parity с reference по tool-call semantics и streaming event handling без изменения архитектурных boundary provider.

## Шаги реализации
- [ ] Сверить mapping tool schemas в [`llm_agent_platform/api/openai/providers/openai_chatgpt.py`](llm_agent_platform/api/openai/providers/openai_chatgpt.py:124) с reference из [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts:208)
- [ ] Добавить parity для MCP tool names и безопасной обработки `call_id` по мотивам [`externel_projects/kilocode/src/utils/mcp-name.ts`](externel_projects/kilocode/src/utils/mcp-name.ts:43) и [`externel_projects/kilocode/src/utils/tool-id.ts`](externel_projects/kilocode/src/utils/tool-id.ts:52)
- [ ] Довести streaming обработку tool delta событий до поведения reference из [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts:842), включая fallback на ранее увиденные `tool_call id/name`
- [ ] Обновить или добавить L1/L2 тесты на MCP branch, sanitized `call_id` и tool-call-only stream scenarios

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Выявлены подтверждённые расхождения между [`llm_agent_platform/api/openai/providers/openai_chatgpt.py`](llm_agent_platform/api/openai/providers/openai_chatgpt.py:1) и reference из [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts:1) по MCP tool schemas, `call_id` sanitation и streaming tool delta fallback.
- Next Step: Реализовать parity-правки в [`llm_agent_platform/api/openai/providers/openai_chatgpt.py`](llm_agent_platform/api/openai/providers/openai_chatgpt.py:1) и зафиксировать их тестами.
- Blockers: зависит от утверждённого плана [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:1); новых Stage 2 blockers не выявлено.
- Contract Changes: none
- Verification: `uv run python -m unittest llm_agent_platform.tests.test_openai_chatgpt_runtime`

# Task: OpenAI ChatGPT parity regression, docs sync and task closure

## Контекст
- Источник: [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:198)
- Связанные артефакты: [`tasks_descriptions/tasks/034-openai-chatgpt-tool-and-streaming-parity.md`](tasks_descriptions/tasks/034-openai-chatgpt-tool-and-streaming-parity.md:1), [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:1), [`tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md`](tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md:1), [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1)

## Architecture Context References
- [ ] [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:41)
- [ ] [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:96)

## Specification References
- [ ] [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:1)
- [ ] [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:44)

## Test Design References
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- [ ] [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1)

## Workflow References
- [ ] `none`

## Цель
- После завершения parity-работ синхронизировать тестовые и документационные артефакты, обновить task status для [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:1) и зафиксировать reproducible verification contour.

## Шаги реализации
- [ ] Собрать regression contour по задачам [`tasks_descriptions/tasks/034-openai-chatgpt-tool-and-streaming-parity.md`](tasks_descriptions/tasks/034-openai-chatgpt-tool-and-streaming-parity.md:1)-[`tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md`](tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md:1)
- [ ] Обновить provider docs и test docs по новым semantics auth-invalid accounts и routing behavior
- [ ] Синхронизировать `Execution Status` в [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:44) и связанных parity-задачах
- [ ] Зафиксировать единый reproducible verification command set и результаты прохождения

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Нужна финальная интеграционная задача, которая закроет документацию, regression contour и handoff после выполнения parity-веток [`tasks_descriptions/tasks/034-openai-chatgpt-tool-and-streaming-parity.md`](tasks_descriptions/tasks/034-openai-chatgpt-tool-and-streaming-parity.md:1)-[`tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md`](tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md:1).
- Next Step: Дождаться завершения зависимых parity-задач и собрать общий regression/doc-sync проход.
- Blockers: зависит от завершения [`tasks_descriptions/tasks/034-openai-chatgpt-tool-and-streaming-parity.md`](tasks_descriptions/tasks/034-openai-chatgpt-tool-and-streaming-parity.md:1), [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:1) и [`tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md`](tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md:1).
- Contract Changes: present
- Verification: `uv run python -m unittest llm_agent_platform.tests.test_openai_chatgpt_runtime llm_agent_platform.tests.test_quota_account_router llm_agent_platform.tests.test_provider_catalogs`

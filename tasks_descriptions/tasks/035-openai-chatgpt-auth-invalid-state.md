# Task: OpenAI ChatGPT auth-invalid state and classification

## Контекст
- Источник: [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:119)
- Связанные артефакты: [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md:23), [`llm_agent_platform/auth/openai_chatgpt_oauth.py`](llm_agent_platform/auth/openai_chatgpt_oauth.py:1), [`externel_projects/kilocode/src/integrations/openai-codex/oauth.ts`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:115), [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py:1)

## Architecture Context References
- [ ] [`docs/auth.md`](docs/auth.md:157)
- [ ] [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)

## Specification References
- [ ] [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:135)
- [ ] [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:60)

## Test Design References
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:10)
- [ ] [`docs/testing/suites/quota-state-persistence.md`](docs/testing/suites/quota-state-persistence.md:1)

## Workflow References
- [ ] `none`

## Цель
- Добавить в runtime явную классификацию OAuth refresh ошибок для `openai-chatgpt` и отдельный auth-health state, который помечает аккаунт как `invalid_grant` без автоудаления credentials.

## Шаги реализации
- [ ] Выделить постоянные OAuth refresh failures по семантике reference из [`externel_projects/kilocode/src/integrations/openai-codex/oauth.ts`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts:126)
- [ ] Спроектировать и реализовать provider-specific auth-health state в runtime boundary, не смешивая его с credentials file
- [ ] Обеспечить запись machine-readable причины, timestamp и operator action с рекомендацией пере-bootstrap через [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py:1)
- [ ] Добавить тесты на различие `invalid_grant` и transient refresh failures, а также на восстановление состояния после успешного reauth

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: План согласован — invalid refresh token не удаляет credentials, а переводит аккаунт в auth-invalid state с рекомендацией повторного bootstrap через [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py:1).
- Next Step: Спроектировать auth-health state envelope и реализовать классификацию ошибок в [`llm_agent_platform/auth/openai_chatgpt_oauth.py`](llm_agent_platform/auth/openai_chatgpt_oauth.py:1).
- Blockers: для materialization state могут потребоваться новые runtime-path helpers рядом с [`llm_agent_platform/services/runtime_state_paths.py`](llm_agent_platform/services/runtime_state_paths.py:1), но Stage 2 gap не выявлен.
- Contract Changes: present
- Verification: `uv run python -m unittest llm_agent_platform.tests.test_openai_chatgpt_runtime`

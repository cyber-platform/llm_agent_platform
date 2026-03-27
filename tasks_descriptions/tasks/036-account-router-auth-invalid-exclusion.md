# Task: Exclude auth-invalid OpenAI ChatGPT accounts from router selection

## Контекст
- Источник: [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:160)
- Связанные артефакты: [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:1), [`llm_agent_platform/services/account_router.py`](llm_agent_platform/services/account_router.py:1), [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)

## Architecture Context References
- [ ] [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)
- [ ] [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)

## Specification References
- [ ] [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:177)
- [ ] [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:1)

## Test Design References
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:10)
- [ ] [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)

## Workflow References
- [ ] `none`

## Цель
- Научить router исключать auth-invalid аккаунты `openai-chatgpt` из selection pool, а при полном выбытии группы возвращать отдельную ошибку `all accounts auth-invalid`.

## Шаги реализации
- [ ] Подключить auth-health state из [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:1) к selection logic в [`llm_agent_platform/services/account_router.py`](llm_agent_platform/services/account_router.py:121)
- [ ] Развести terminal states `quota exhausted`, `cooldown` и `auth-invalid` для `single` и `rounding` режимов
- [ ] Обеспечить игнорирование auth-invalid accounts при rotation без изменения поведения для здоровых аккаунтов
- [ ] Добавить тесты на mixed pools и на полный auth-invalid pool с ожидаемой ошибкой `all accounts auth-invalid`

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Operational policy согласована — auth-invalid accounts не используются в routing, а при полном выбытии группы должен возвращаться отдельный terminal state `all accounts auth-invalid`.
- Next Step: Реализовать чтение auth-health state в [`llm_agent_platform/services/account_router.py`](llm_agent_platform/services/account_router.py:1) и развести terminal errors для `single|rounding`.
- Blockers: зависит от state boundary из [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:1).
- Contract Changes: present
- Verification: `uv run python -m unittest llm_agent_platform.tests.test_quota_account_router llm_agent_platform.tests.test_openai_chatgpt_runtime`

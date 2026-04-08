# Task: Migrate Qwen storage/state/secrets naming to kebab-case

## Контекст
- Источник: follow-up после реализации [`operational_scope/tasks/016-gpt-integration.md`](operational_scope/tasks/016-gpt-integration.md:1) и унификации storage naming для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1)
- Связанные артефакты: [`llm_agent_platform/services/credentials_paths.py`](llm_agent_platform/services/credentials_paths.py:7), [`llm_agent_platform/services/account_state_store.py`](llm_agent_platform/services/account_state_store.py:39), [`llm_agent_platform/services/account_router.py`](llm_agent_platform/services/account_router.py:614), [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1), [`docs/configuration/provider-accounts-config.md`](docs/configuration/provider-accounts-config.md:1), [`docs/auth.md`](docs/auth.md:1), [`docs/examples/qwen_accounts_config.example.json`](docs/examples/qwen_accounts_config.example.json:1)

## Architecture Context References
- [ ] [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
- [ ] [`docs/adr/0019-state-dir-unified-account-state-and-async-writer.md`](docs/adr/0019-state-dir-unified-account-state-and-async-writer.md:1)

## Specification References
- [ ] [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)
- [ ] [`docs/configuration/provider-accounts-config.md`](docs/configuration/provider-accounts-config.md:1)

## Test Design References
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- [ ] [`docs/testing/suites/config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md:1)

## Workflow References
- [ ] `none`

## Цель
- Перевести Qwen storage namespace с `qwen_code` на `qwen-code`, чтобы все provider storage/state/secrets директории использовали единый kebab-case канон.

## Шаги реализации
- [ ] Провести полный inventory всех упоминаний `qwen_code` и разделить их на internal code id, public provider id и storage/state/secrets namespace
- [ ] Перевести storage paths, env defaults, accounts configs, docs examples и runtime state paths с `qwen_code` на `qwen-code`
- [ ] Убрать special-case нормализацию для Qwen из [`llm_agent_platform/services/credentials_paths.py`](llm_agent_platform/services/credentials_paths.py:7), если после миграции она больше не нужна
- [ ] Обновить документацию по layout и operator-facing конфигурации в [`docs/`](docs:1)
- [ ] Обновить и прогнать тесты, чувствительные к storage/state layout и provider config paths
- [ ] Зафиксировать, нужны ли одноразовые migration/deletion steps для legacy state в `STATE_DIR`

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Follow-up задача создана. Текущий storage canon уже переведён на kebab-case для [`gemini-cli`](secrets/gemini-cli:1) и [`openai-chatgpt`](secrets/openai-chatgpt:1), но для Qwen в storage namespace всё ещё используется [`qwen_code`](secrets/qwen_code:1).
- Next Step: Выполнить inventory всех вхождений `qwen_code` и подготовить безопасную migration map `qwen_code -> qwen-code` для secrets/state/docs/tests.
- Blockers: none
- Contract Changes: present
- Verification: `uv run python -m unittest llm_agent_platform/tests/test_quota_account_router.py llm_agent_platform/tests/test_refactor_p2_routes.py`

# Task: Provider contracts and catalog foundation

## Контекст
- Источник: [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1)
- Связанные артефакты: [`docs/contracts/config/provider-descriptor.schema.json`](docs/contracts/config/provider-descriptor.schema.json:1), [`docs/contracts/config/provider-registry.schema.json`](docs/contracts/config/provider-registry.schema.json:1), [`docs/contracts/state/provider-catalog-snapshot.schema.json`](docs/contracts/state/provider-catalog-snapshot.schema.json:1), [`docs/providers/README.md`](docs/providers/README.md:1)

## Architecture Context References
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:23)
- [ ] [`docs/architecture/component-map.md`](docs/architecture/component-map.md:74)

## Specification References
- [ ] [`docs/contracts/config/provider-descriptor.schema.json`](docs/contracts/config/provider-descriptor.schema.json:1)
- [ ] [`docs/contracts/state/provider-catalog-snapshot.schema.json`](docs/contracts/state/provider-catalog-snapshot.schema.json:1)

## Test Design References
- [ ] [`docs/testing/suites/provider-catalogs.md`](docs/testing/suites/provider-catalogs.md:1)
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Workflow References
- [ ] `none`

## Цель
- Зафиксировать и реализовать contract-first основу provider-centric платформы: provider descriptor, provider registry, provider catalog snapshot и правила их хранения.

## Шаги реализации
- [x] Создать schema-файлы для `provider-descriptor`, `provider-registry` и `provider-catalog-snapshot` в [`docs/contracts/`](docs/contracts:1)
- [x] Согласовать канонический `provider_id` в kebab-case для `gemini-cli`, `google-vertex`, `qwen-code`, `openai-chatgpt`
- [x] Зафиксировать путь хранения `catalog snapshot` в `STATE_DIR` только для discovery-capable providers
- [x] Подготовить runtime foundation для загрузки provider registry и catalog contracts без route hardcode
- [x] Обновить связанные архитектурные ссылки, если contract names или storage layout меняются по факту реализации

## Definition of Done
- [x] Изменения реализованы по спецификации
- [x] Проверки пройдены
- [x] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Contract-first foundation реализован полностью: созданы [`docs/contracts/config/provider-descriptor.schema.json`](docs/contracts/config/provider-descriptor.schema.json:1), [`docs/contracts/config/provider-registry.schema.json`](docs/contracts/config/provider-registry.schema.json:1), [`docs/contracts/state/provider-catalog-snapshot.schema.json`](docs/contracts/state/provider-catalog-snapshot.schema.json:1); добавлен minimal runtime foundation в [`llm_agent_platform/services/provider_registry.py`](llm_agent_platform/services/provider_registry.py:1) и bootstrap registry data в [`llm_agent_platform/provider_registry/registry.json`](llm_agent_platform/provider_registry/registry.json:1) с provider descriptors в [`llm_agent_platform/provider_registry/providers/gemini-cli.json`](llm_agent_platform/provider_registry/providers/gemini-cli.json:1), [`llm_agent_platform/provider_registry/providers/google-vertex.json`](llm_agent_platform/provider_registry/providers/google-vertex.json:1), [`llm_agent_platform/provider_registry/providers/qwen-code.json`](llm_agent_platform/provider_registry/providers/qwen-code.json:1), [`llm_agent_platform/provider_registry/providers/openai-chatgpt.json`](llm_agent_platform/provider_registry/providers/openai-chatgpt.json:1); bootstrap catalogs исправлены на true model ids без suffix `quota`/`vertex`, а provider distinctions вынесены в `metadata`
- Next Step: Использовать registry foundation для provider-centric routing и discovery path в [`tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md`](tasks_descriptions/tasks/027-provider-centric-routing-and-openai-chatgpt-provider.md:1)
- Blockers: none
- Contract Changes: present
- Verification: `uv run python - <<'PY' ... json.load(...) ... PY` для [`docs/contracts/config/provider-descriptor.schema.json`](docs/contracts/config/provider-descriptor.schema.json:1), [`docs/contracts/config/provider-registry.schema.json`](docs/contracts/config/provider-registry.schema.json:1), [`docs/contracts/state/provider-catalog-snapshot.schema.json`](docs/contracts/state/provider-catalog-snapshot.schema.json:1) — success; `uv run python -m unittest llm_agent_platform.tests.test_refactor_p2_routes llm_agent_platform.tests.test_openai_contract` — success (`Ran 16 tests`, `OK`)

# Task: Mark legacy docs as historical context and sync outdated narrative

## Контекст
- Источник: cleanup после переноса Source of Truth в [`docs/`](docs:1)
- Связанные артефакты: [`docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1), [`docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md`](docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md:1), [`docs/adr/0017-url-prefix-groups-and-group-aware-models.md`](docs/adr/0017-url-prefix-groups-and-group-aware-models.md:1), [`docs/testing/suites/config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md:1), [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1), [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)

## Architecture Context References
- [ ] [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1)
- [ ] [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)

## Specification References
- [ ] [`docs/vision.md`](docs/vision.md:1)
- [ ] [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)

## Test Design References
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- [ ] [`docs/testing/suites/config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md:1)

## Workflow References
- [ ] `none`

## Цель
- Убрать из [`docs/`](docs:1) устаревшие narrative и несогласованные страницы, оставив только актуальный канон без режима historical context.

## Шаги реализации
- [x] Проанализировать документы [`docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1), [`docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md`](docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md:1), [`docs/adr/0017-url-prefix-groups-and-group-aware-models.md`](docs/adr/0017-url-prefix-groups-and-group-aware-models.md:1), [`docs/testing/suites/config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md:1) на предмет расхождений с текущим SoT
- [x] Для каждого документа принять решение: обновить до текущего канона или удалить, если он больше не нужен
- [x] Синхронизировать формулировки про layout, routing, bootstrap scripts и testing narrative с актуальными документами [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1), [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1), [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- [x] Удалить или переписать все оставшиеся страницы, которые сохраняют устаревший narrative внутри [`docs/`](docs:1)
- [x] Проверить, что внутри [`docs/`](docs:1) не осталось двусмысленных ссылок на устаревший канон

## Definition of Done
- [x] Изменения реализованы по спецификации
- [x] Проверки пройдены: выполнен grep/review по [`docs/`](docs:1) на legacy narrative, проверены перекрестные ссылки, подтверждено что внутри [`docs/`](docs:1) остался только актуальный канон
- [x] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Legacy cleanup выполнен: [`docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md`](docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md:1) переписан под фактический layout, [`docs/adr/0017-url-prefix-groups-and-group-aware-models.md`](docs/adr/0017-url-prefix-groups-and-group-aware-models.md:1) помечен как superseded, [`docs/testing/suites/config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md:1) и связанные docs синхронизированы с active SoT.
- Next Step: Поддерживать [`docs/`](docs:1) как единственный active SoT и не возвращать historical narrative в новые task/docs updates.
- Blockers: none
- Contract Changes: none
- Verification: grep/review по [`docs/`](docs:1) на legacy narrative и подтверждение что в итоговой структуре остались только актуальные документы

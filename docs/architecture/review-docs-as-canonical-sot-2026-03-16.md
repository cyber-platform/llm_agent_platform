# Mini Architect Stage Review (warn-only): docs as canonical SoT

Дата: 2026-03-16
Strictness: warn-only

## Goal
Зафиксировать формальный review gate для изменения: `docs/` становятся самодостаточным каноном реализованного функционала и не зависят от временных артефактов.

Фокус review: качество канона, навигации и ссылочной целостности в [`docs/`](docs:1).

## Reviewed artifacts (SoT)

### Architecture
- Компонентная карта: [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
- OpenAI chat_completions pipeline: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
- Quota rotation + groups + models: [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)

### ADR
- [`docs/adr/0014-stream-state-container-and-429-rotation-policy.md`](docs/adr/0014-stream-state-container-and-429-rotation-policy.md:1)
- [`docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1)
- [`docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md`](docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md:1)
- [`docs/adr/0017-url-prefix-groups-and-group-aware-models.md`](docs/adr/0017-url-prefix-groups-and-group-aware-models.md:1)

### Contracts
- 429 error schema: [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1)

### Testing knowledge base
- Test map: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- Suites:
  - [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1)
  - [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)
  - [`docs/testing/suites/quota-parity.md`](docs/testing/suites/quota-parity.md:1)
  - [`docs/testing/suites/proxy-routes.md`](docs/testing/suites/proxy-routes.md:1)
  - [`docs/testing/suites/config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md:1)

## DoD checklist (adapted)
Ниже — формальный проход по DoD (адаптирован под цель «docs as SoT»).

1) Spec по skeleton
- Status: WARN
- Notes: нет отдельного единого spec-документа по skeleton; роль SoT исполняют страницы в [`docs/architecture/`](docs/architecture:1) и ADR.

2) Stable requirement IDs (`US-*`, `NFR-*`...)
- Status: WARN
- Notes: для канона реализованного функционала requirement-IDs не нормализованы как единый реестр; часть suites содержит сценарии уровня test design без явного реестра требований.

3) Диаграммы отражают реальные границы и ключевые сценарии
- Status: PASS
- Evidence:
  - компонентные границы: [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
  - ключевые потоки: [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)

4) Contracts зафиксированы и связаны
- Status: PASS
- Evidence: [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1) связан из архитектуры и ADR.

5) Contract quality gate
- Status: WARN
- Notes: автоматизированная валидация/линт контрактов не зафиксирована как команда в документации; требуется добавить команду validate/lint (или ссылку на существующую) в тест-контур.

6) Test design coverage
- Status: PASS-WARN
- Evidence: есть test map и suite-страницы.
- Notes: coverage matrix присутствует точечно; не все suites имеют явную матрицу требований.

7) Risk register
- Status: WARN
- Notes: отдельный risk register отсутствует; риски частично отражены в ADR (trade-offs/последствия), но не централизованы.

8) ADR по триггерам
- Status: PASS
- Evidence: набор ADR в [`docs/adr/`](docs/adr:1) покрывает ключевые trade-offs и изменения границ (stream state, env split, groups/models).

9) Open questions
- Status: PASS-WARN
- Notes: явный реестр Open Questions отсутствует; вопросы должны фиксироваться либо в ADR, либо в отдельной странице `open-questions` при необходимости.

10) Link integrity (no hidden deps)
- Status: PASS
- Evidence: в [`docs/`](docs:1) отсутствуют ссылки на каталоги временных артефактов; навигация обеспечивается через architecture/adr/contracts/testing.

## Verdict
**PASS-WITH-WARNINGS** (warn-only)

## Required actions (to reach stronger PASS)
1) Добавить contract validation/lint команду (и место, где она выполняется) в тестовый канон: [`docs/testing/test-map.md`](docs/testing/test-map.md:1).
2) Если нужен «полный» Architect Stage gate: завести единый spec + risk register (или явно решить, что для канона реализованного функционала это не требуется).


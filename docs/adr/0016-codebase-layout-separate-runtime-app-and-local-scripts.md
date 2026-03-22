# ADR 0016: Runtime package layout `llm_agent_platform/` + local scripts in `scripts/`

## Status
Accepted

## Context

Платформа должна иметь явные границы между:

- runtime-кодом контейнерного приложения;
- локальными bootstrap и utility scripts;
- внешними nested repos, которые используются только как upstream/reference.

Ранний проектный narrative допускал перенос всего кода в `src/`, но этот вариант не является актуальным Source of Truth и не должен использоваться в active documentation.

Актуальный runtime layout уже сложился и используется во всей текущей архитектуре платформы:

- runtime package: [`llm_agent_platform/`](llm_agent_platform:1)
- local scripts: [`scripts/`](scripts:1)
- canonical docs and contracts: [`docs/`](docs:1)
- external nested repos: [`gemini-cli/`](gemini-cli:1), [`qwen-code/`](qwen-code:1), [`kilocode/`](kilocode:1)

Это соответствует provider-centric канону и уменьшает смешение между runtime, bootstrap и reference-кодом.

## Decision

Принять фактический layout как канонический:

1. [`llm_agent_platform/`](llm_agent_platform:1) — единственный runtime package платформы.
2. [`scripts/`](scripts:1) — локальные bootstrap/maintenance scripts, не являющиеся частью контейнерного runtime.
3. [`docs/`](docs:1) — Source of Truth для архитектуры, contracts и testing traceability.
4. Внешние nested repos остаются reference-only и не описываются как runtime-компоненты платформы.

### Canonical layout

- [`llm_agent_platform/`](llm_agent_platform:1)
  - runtime API, auth, core, services, config и entrypoint
- [`scripts/`](scripts:1)
  - bootstrap OAuth и вспомогательные локальные скрипты
- [`docs/`](docs:1)
  - архитектурный канон, ADR, contracts, testing docs

### Entry points

- Контейнерный runtime стартует через пакет [`llm_agent_platform/__main__.py`](llm_agent_platform/__main__.py:1).
- Локальные bootstrap scripts запускаются из [`scripts/`](scripts:1).

## Options considered

### Option A: Сохранить старый плоский narrative
- Плюсы: не требуются правки документации.
- Минусы: active docs расходятся с фактическим layout и ломают навигацию.

### Option B: Перенести всё в `src/`
- Плюсы: классический packaging narrative.
- Минусы: не соответствует текущему runtime и создаёт ложный Source of Truth.

### Option C: Канонизировать фактический layout `llm_agent_platform/` + `scripts/`
- Плюсы: документация совпадает с реальной структурой проекта; меньше когнитивного шума; проще traceability.
- Минусы: требуется cleanup legacy docs, где остались ссылки на `src/` и `model_proxy`.

## Consequences

### Positive
- Runtime boundary совпадает с текущей реализацией.
- Scripts boundary совпадает с bootstrap workflow.
- Архитектурные и testing документы могут ссылаться на реальные пути.

### Negative
- Нужно пометить и убрать устаревший `src/` narrative из связанных документов.

## Related canonical documents

- Layout and component map: [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
- Env boundaries: [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)
- Auth bootstrap docs: [`docs/auth.md`](docs/auth.md:1)

## Review conditions

- Пересмотреть ADR, если runtime package будет реально вынесен из [`llm_agent_platform/`](llm_agent_platform:1) в другой layout.

# Task: Bootstrap тестового контура для прокси

## Контекст
- Источник: [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- Связанные артефакты: [`003-api-performance.md`](tasks_descriptions/backlog/003-api-performance.md), [`004-audit-transformation.md`](tasks_descriptions/backlog/004-audit-transformation.md)

## Architecture Context References
- [ ] [`systemPatterns.md`](.kilocode/rules/memory-bank/systemPatterns.md)
- [ ] [`active.md`](.kilocode/rules/memory-bank/active.md)

## Specification References
- [ ] [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- [ ] `none` (contract schema/OpenAPI пока не выделен)

## Test Design References
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md) (gap: отсутствует, создать в рамках задачи)
- [ ] [`tasks_descriptions/tasks/`](tasks_descriptions/tasks/) (L1-L4 трассировка задач)

## Workflow References
- [ ] `none`

## Цель
- Создать канонический индекс тестового контура и базовые suite-страницы для дальнейших задач parity/compatibility.

## Шаги реализации
- [ ] Создать [`docs/testing/test-map.md`](docs/testing/test-map.md) с разделами по OpenAI-compatible и Google Gemini parity.
- [ ] Создать suite-страницы в [`docs/testing/suites/`](docs/testing/suites/) для stream/non-stream/tool-calling.
- [ ] Зафиксировать трассировку `requirement -> suite -> test script` для задач 007-011.

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: задача создана, реализация не начата.
- Next Step: создать [`docs/testing/test-map.md`](docs/testing/test-map.md).
- Blockers: none.
- Contract Changes: none.
- Verification: not started.


# Task: Native Google Gemini routing + parity тесты

## Контекст
- Источник: [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- Связанные артефакты: [`api/gemini/routes.py`](api/gemini/routes.py), [`kilocode/src/api/providers/gemini.ts`](kilocode/src/api/providers/gemini.ts)

## Architecture Context References
- [ ] [`systemPatterns.md`](.kilocode/rules/memory-bank/systemPatterns.md)
- [ ] [`active.md`](.kilocode/rules/memory-bank/active.md)

## Specification References
- [ ] [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- [ ] `none`

## Test Design References
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md)
- [ ] [`docs/testing/suites/`](docs/testing/suites/)

## Workflow References
- [ ] `none`

## Цель
- Сделать надёжный native путь для профиля **Google Gemini** через custom base URL прокси и проверить parity-поведение.

## Шаги реализации
- [ ] Добавить явное управление режимом quota/vertex в native Gemini роуте (не только через суффикс модели).
- [ ] Убедиться, что `generateContent/streamGenerateContent` корректно проксируются для профиля Google Gemini.
- [ ] Добавить тесты на native stream/non-stream и ошибки.
- [ ] Добавить parity-тесты на структуру данных (SSE/JSON), ожидаемую клиентом.
- [ ] Обновить test-map/suite документацию.

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: задача создана, реализация не начата.
- Next Step: определить интерфейс явного переключения quota/vertex для native роутов.
- Blockers: none.
- Contract Changes: none.
- Verification: not started.


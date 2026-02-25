# Task: Core transport parity с Google Gemini CLI (strict режим)

## Контекст
- Источник: [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- Связанные артефакты: [`api/openai/routes.py`](api/openai/routes.py), [`api/gemini/routes.py`](api/gemini/routes.py), [`api/openai/transform.py`](api/openai/transform.py)

## Architecture Context References
- [ ] [`systemPatterns.md`](.kilocode/rules/memory-bank/systemPatterns.md)
- [ ] [`active.md`](.kilocode/rules/memory-bank/active.md)

## Specification References
- [ ] [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- [ ] `none`

## Test Design References
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md)
- [ ] [`tasks_descriptions/tasks/010-gemini-native-routing-and-parity-tests.md`](tasks_descriptions/tasks/010-gemini-native-routing-and-parity-tests.md)

## Workflow References
- [ ] `none`

## Цель
- Сконцентрировать логику quota transport в едином модуле и включить strict parity режим без прокси-эвристик.

## Шаги реализации
- [ ] Вынести Cloud Code transport в отдельный модуль/сервис и подключить его из OpenAI/Gemini роутеров.
- [ ] Ввести конфиг-флаг strict parity и отключить в этом режиме fallback chain моделей.
- [ ] Убрать/отключить bypass-инъекцию `thoughtSignature` в strict parity режиме.
- [ ] Унифицировать обработку stream/non-stream ошибок Cloud Code.
- [ ] Добавить минимальные parity-тесты transport shape.

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: задача создана, реализация не начата.
- Next Step: спроектировать API нового transport-модуля и точки интеграции в роуты.
- Blockers: none.
- Contract Changes: none.
- Verification: not started.


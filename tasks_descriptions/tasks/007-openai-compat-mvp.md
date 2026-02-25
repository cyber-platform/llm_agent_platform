# Task: OpenAI Compatible MVP для Kilo Code/OpenCode

## Контекст
- Источник: [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- Связанные артефакты: [`api/openai/routes.py`](api/openai/routes.py), [`core/utils.py`](core/utils.py)

## Architecture Context References
- [ ] [`systemPatterns.md`](.kilocode/rules/memory-bank/systemPatterns.md)
- [ ] [`active.md`](.kilocode/rules/memory-bank/active.md)

## Specification References
- [ ] [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- [ ] `none` (контрактная схема пока не вынесена в отдельный OpenAPI)

## Test Design References
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md) (создаётся в задаче [`006-test-map-bootstrap.md`](tasks_descriptions/tasks/006-test-map-bootstrap.md))
- [ ] [`tasks_descriptions/tasks/008-openai-stream-and-contract-tests.md`](tasks_descriptions/tasks/008-openai-stream-and-contract-tests.md)

## Workflow References
- [ ] `none`

## Цель
- Довести OpenAI-совместимость прокси до рабочего MVP, достаточного для стабильной интеграции с Kilo Code/OpenCode.

## Шаги реализации
- [ ] Добавить корректную обработку `max_completion_tokens` и `max_tokens` (с приоритетом modern поля) в [`chat_completions()`](api/openai/routes.py:16).
- [ ] Убрать принудительный дефолт `maxOutputTokens=65535` в [`chat_completions()`](api/openai/routes.py:36), если лимит не передан клиентом.
- [ ] Унифицировать non-stream OpenAI response для quota/vertex в [`chat_completions()`](api/openai/routes.py:330).
- [ ] Привести ошибки upstream к консистентному OpenAI error shape через [`create_openai_error()`](core/utils.py:55).
- [ ] Подготовить конфигурируемый список моделей в [`list_models()`](api/openai/routes.py:455).

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: задача создана, реализация не начата.
- Next Step: реализовать поддержку `max_completion_tokens` в [`chat_completions()`](api/openai/routes.py:16).
- Blockers: none.
- Contract Changes: none.
- Verification: not started.


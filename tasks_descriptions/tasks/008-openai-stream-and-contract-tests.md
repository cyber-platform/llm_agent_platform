# Task: Контрактные тесты OpenAI-compatible (stream/non-stream/tools/usage)

## Контекст
- Источник: [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- Связанные артефакты: [`007-openai-compat-mvp.md`](tasks_descriptions/tasks/007-openai-compat-mvp.md), [`api/openai/routes.py`](api/openai/routes.py)

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
- Закрепить OpenAI-контракт прокси воспроизводимыми тестами для клиентов Kilo Code/OpenCode.

## Шаги реализации
- [ ] Добавить тесты non-stream ответа: текст, tool_calls, finish_reason, usage.
- [ ] Добавить тесты stream SSE: delta content, tool_calls chunks, `[DONE]`.
- [ ] Добавить тест на `stream_options.include_usage=true` и финальный usage chunk.
- [ ] Добавить тесты маппинга ошибок upstream -> OpenAI error format.
- [ ] Обновить индекс тестов и suite-страницы.

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: задача создана, реализация не начата.
- Next Step: подготовить suite-страницу для OpenAI stream/non-stream контрактов.
- Blockers: none.
- Contract Changes: none.
- Verification: not started.


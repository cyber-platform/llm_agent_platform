# Task: Добавить проверку last_used_at для Qwen streaming и унифицировать secrets_test

## Контекст
- Источник: запрос на покрытие кейса отсутствия `last_used_at.json` в streaming для Qwen и перевод тестов на фиктивные файлы `secrets_test/`.
- Связанные артефакты: [`docs/auth.md`](docs/auth.md:98), [`api/openai/providers/qwen_code.py`](api/openai/providers/qwen_code.py:131).

## Architecture Context References
- [x] Persisted state и quota reset: [`docs/architecture/quota-reset-periods-and-account-state.md`](docs/architecture/quota-reset-periods-and-account-state.md:1)
- [x] OpenAI pipeline: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)

## Specification References
- [x] Контракт `last_used_at`: [`docs/contracts/state/account-last-used.schema.json`](docs/contracts/state/account-last-used.schema.json:1)
- [x] Runtime state paths: [`docs/auth.md`](docs/auth.md:98)

## Test Design References
- [x] Suite `openai-contract`: [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1)
- [x] Test map: [`docs/testing/test-map.md`](docs/testing/test-map.md:7)

## Workflow References
- [x] none

## Цель
- Зафиксировать тест на запись `last_used_at` в Qwen streaming и перевести тесты на фиктивные `secrets_test/` файлы.

## Шаги реализации
- [x] Добавить тест Qwen streaming для `last_used_at`.
- [x] Перевести тестовые конфиги/credentials на `secrets_test/`.
- [x] Обновить suite/test-map документацию.

## Definition of Done
- [x] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [x] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: добавлен тест `test_qwen_stream_persists_last_used`, тесты переведены на `secrets_test/` и сидятся фиктивные credentials; suite/test-map обновлены.
- Next Step: выполнить `uv run python -m unittest discover -s tests -p "test_*.py"`.
- Blockers: none
- Contract Changes: none
- Verification: не запускалось

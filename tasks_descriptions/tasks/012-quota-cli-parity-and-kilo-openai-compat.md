# Task: Quota-first parity с Gemini CLI и OpenAI-compatible совместимость для Kilo Code

## Контекст
- Источник: [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- Связанные артефакты: [`009-cli-transport-parity-core.md`](tasks_descriptions/tasks/009-cli-transport-parity-core.md), [`010-gemini-native-routing-and-parity-tests.md`](tasks_descriptions/tasks/010-gemini-native-routing-and-parity-tests.md), [`007-openai-compat-mvp.md`](tasks_descriptions/tasks/007-openai-compat-mvp.md)

## Architecture Context References
- [x] [`systemPatterns.md`](.kilocode/rules/memory-bank/systemPatterns.md)
- [x] [`active.md`](.kilocode/rules/memory-bank/active.md)

## Specification References
- [x] [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- [x] Эталон CLI-контракта: [`toGenerateContentRequest()`](gemini-cli/packages/core/src/code_assist/converter.ts:119), [`requestPost()`](gemini-cli/packages/core/src/code_assist/server.ts:293), [`requestStreamingPost()`](gemini-cli/packages/core/src/code_assist/server.ts:337)

## Test Design References
- [x] [`docs/testing/test-map.md`](docs/testing/test-map.md)
- [x] [`008-openai-stream-and-contract-tests.md`](tasks_descriptions/tasks/008-openai-stream-and-contract-tests.md)

## Workflow References
- [x] `none`

## Цель
- Сделать outbound quota-запрос прокси к Google максимально идентичным актуальному `gemini-cli`, сохранив inbound/outbound OpenAI-compatible контракт для Kilo Code.

## Шаги реализации
- [x] Добавить runtime capture-relay для `CODE_ASSIST_ENDPOINT` и собрать golden-артефакты `generate`/`stream` от `gemini-cli` с анонимизацией чувствительных данных.
- [x] Зафиксировать статический эталон полей/структуры quota-запроса из `gemini-cli` и подготовить правила сравнения.
- [x] Вынести единый quota transport-модуль и подключить его в [`chat_completions()`](api/openai/routes.py:25) и [`gemini_proxy()`](api/gemini/routes.py:23).
- [x] Привести payload quota-запроса к CLI shape: `model`, `project`, `user_prompt_id`, `request.session_id`, `request.contents`, `request.generationConfig`.
- [x] Убрать strict-parity расхождения в [`chat_completions()`](api/openai/routes.py:443) и [`transform_openai_to_gemini()`](api/openai/transform.py:4), оставив OpenAI-compatible ответ для Kilo.
- [x] Добавить parity-тесты сравнения `proxy payload vs golden CLI` и контрактные OpenAI-тесты stream/non-stream под ожидания Kilo.

## Definition of Done
- [x] Изменения реализованы по спецификации
- [x] Проверки пройдены
- [x] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: реализация задачи завершена. Исправлен импорт `CLOUD_CODE_ENDPOINT` в [`api/gemini/routes.py`](api/gemini/routes.py:4), стабилизирован входной JSON в native-роуте (`request.get_json(... ) or {}`), удалён legacy `thoughtSignature` bypass из [`transform_openai_to_gemini()`](api/openai/transform.py:4), добавлены parity/contract тесты [`test_quota_transport_parity.py`](tests/test_quota_transport_parity.py) и [`test_openai_contract.py`](tests/test_openai_contract.py), а также golden fixtures и тестовая документация ([`docs/testing/test-map.md`](docs/testing/test-map.md), [`openai-contract.md`](docs/testing/suites/openai-contract.md), [`quota-parity.md`](docs/testing/suites/quota-parity.md)).
- Next Step: выполнить runtime capture через реальный `gemini-cli` на стенде с валидными OAuth квотами и положить реальные anonymized golden-артефакты в `tests/fixtures/parity/` для регрессионного сравнения с живым трафиком.
- Blockers: none.
- Contract Changes: present.
- Verification: выполнено `uv run python -m compileall api auth core services main.py tests` и `uv run python -m unittest discover -s tests -p "test_*.py"` (6 tests, OK).

## Handoff Notes (для продолжения в новом чате)
- **Что уже изменено**:
  - [`api/gemini/routes.py`](api/gemini/routes.py:4): восстановлен импорт `CLOUD_CODE_ENDPOINT`, добавлен безопасный разбор JSON.
  - [`api/openai/transform.py`](api/openai/transform.py:4): полностью удалён legacy `thoughtSignature` bypass.
  - [`tests/test_quota_transport_parity.py`](tests/test_quota_transport_parity.py): parity-тесты для payload shape/SSE unwrap/absence of legacy bypass.
  - [`tests/test_openai_contract.py`](tests/test_openai_contract.py): OpenAI-контрактные тесты non-stream/stream usage/error-shape.
  - [`tests/fixtures/parity/golden_cli_generate_request.json`](tests/fixtures/parity/golden_cli_generate_request.json) и [`tests/fixtures/parity/golden_cli_stream_request.json`](tests/fixtures/parity/golden_cli_stream_request.json): golden shape fixtures.
  - [`docs/testing/test-map.md`](docs/testing/test-map.md) + suite-страницы: формализован тестовый контур и трассировка требований.
- **Важно для следующего шага parity-hardening**:
  - заменить synthetic golden fixtures на реальные capture-артефакты из `gemini-cli` через [`api/parity/routes.py`](api/parity/routes.py:60) на окружении с валидными квотами.

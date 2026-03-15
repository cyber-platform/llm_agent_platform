# Task: Произвести рефакторинг проекта

## Контекст

Мы хотим улучшить Modifiability:
- Extensibility
- Maintainability
- Testability
- Deployability

## Refactor Proposals

### P0 (сразу)
1. Устранить import-break в `api/openai/routes.py`: удалить мёртвый импорт `get_user_creds` или восстановить совместимый API в `auth/credentials.py`.
2. Унифицировать логирование: заменить `print()` и `traceback.print_exc()` на единый `logger` из `core/logging.py`.
3. Убрать bare `except` в `api/openai/transform.py`, добавить явные типы исключений и диагностические сообщения.

### P1 (основной рефактор)
1. Декомпозировать `chat_completions()` в `api/openai/routes.py` на pipeline-шаги:
   - parse/validate request,
   - provider strategy selection,
   - upstream execution,
   - response shaping.
2. Вынести provider-specific ветки (Gemini quota / Qwen quota / Vertex) в отдельные стратегии/модули.
3. Убрать дублирование stream chunk-mapping между quota и non-quota ветками.

### P2 (укрепление качества)
1. Добавить smoke-тест импорта приложения и endpoint-тесты `/v1/models`.
2. Добавить тесты для native Gemini proxy (`api/gemini/routes.py`) и parity relay (`api/parity/routes.py`).
3. Пересмотреть `config.py`: убрать чувствительные дефолты из кода, опираться на env/секреты.

## Execution Status

- **Current State**: P1/P0/P2 завершены. Providers/Strategies/Pipeline внедрены, контракт stream/non-stream подтверждён тестами OpenAI, P0/P2 закрыты, верификация пройдена.
  - Типы контекста и ошибки: [`api/openai/types.py`](api/openai/types.py:1)
  - Pipeline: [`api/openai/pipeline.py`](api/openai/pipeline.py:1)
  - Providers: [`api/openai/providers/base.py`](api/openai/providers/base.py:1), [`api/openai/providers/google_vertex.py`](api/openai/providers/google_vertex.py:1), [`api/openai/providers/gemini_cli.py`](api/openai/providers/gemini_cli.py:1), [`api/openai/providers/qwen_code.py`](api/openai/providers/qwen_code.py:1)
  - Strategies: [`api/openai/strategies/base.py`](api/openai/strategies/base.py:1), [`api/openai/strategies/direct.py`](api/openai/strategies/direct.py:1), [`api/openai/strategies/rotate_on_429_rounding.py`](api/openai/strategies/rotate_on_429_rounding.py:1), [`api/openai/strategies/registry.py`](api/openai/strategies/registry.py:1)
  - Streaming/response shaping: [`api/openai/streaming.py`](api/openai/streaming.py:1), [`api/openai/response_shaper.py`](api/openai/response_shaper.py:1)
  - Роут `chat_completions` переведён на pipeline/strategy оркестрацию: [`api/openai/routes.py`](api/openai/routes.py:1)
  - Обновлены моки в тестах OpenAI контракта: [`tests/test_openai_contract.py`](tests/test_openai_contract.py:1)
- **Next Step**: Перейти к задачам 019/020.
- **Blockers**: none
- **Contract Changes**: none
- **Verification**: `uv run python -m compileall api auth core services main.py tests`; `uv run python -m unittest discover -s tests -p "test_*.py"` (`Ran 24 tests`, `OK`).

## Handoff Notes

### What is done
- Созданы базовые модули P1:
  - [`api/openai/types.py`](api/openai/types.py:1)
  - [`api/openai/pipeline.py`](api/openai/pipeline.py:1)
  - [`api/openai/streaming.py`](api/openai/streaming.py:1)
  - [`api/openai/response_shaper.py`](api/openai/response_shaper.py:1)
- Добавлены Providers:
  - [`api/openai/providers/base.py`](api/openai/providers/base.py:1)
  - [`api/openai/providers/google_vertex.py`](api/openai/providers/google_vertex.py:1)
  - [`api/openai/providers/gemini_cli.py`](api/openai/providers/gemini_cli.py:1)
  - [`api/openai/providers/qwen_code.py`](api/openai/providers/qwen_code.py:1)
- Добавлены Strategies:
  - [`api/openai/strategies/base.py`](api/openai/strategies/base.py:1)
  - [`api/openai/strategies/direct.py`](api/openai/strategies/direct.py:1)
  - [`api/openai/strategies/rotate_on_429_rounding.py`](api/openai/strategies/rotate_on_429_rounding.py:1)
  - [`api/openai/strategies/registry.py`](api/openai/strategies/registry.py:1)
- `chat_completions` переведён на оркестрацию pipeline/strategy: [`api/openai/routes.py`](api/openai/routes.py:1)
- Обновлены моки тестов OpenAI контракта под новые модули: [`tests/test_openai_contract.py`](tests/test_openai_contract.py:1)

### Immediate fix first
- Верификация выполнена, ошибок импорта/моков не выявлено.

### Pending work
1. Нет.

### Commands to run
- `uv run python -m compileall api auth core services main.py tests`
- `uv run python -m unittest discover -s tests -p "test_*.py"`

### User constraints
- Использовать `uv` как основной инструмент запуска/сборки Python.
- Сохранять quota-first и OpenAI-compatible контракт.
- Providers и Strategies должны быть разделены (Providers в `api/openai/providers`, Strategies в `api/openai/strategies`).
- `qwen_oauth` переименован в `qwen_code`.
- Credential Acquisition выполняется bootstrap-скриптами [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py:1) и [`scripts/get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py:1).

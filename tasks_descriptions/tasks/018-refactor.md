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

- **Current State**: Выполнены P0-правки: устранён import-break (`get_user_creds`), унифицировано error/logging в OpenAI/Gemini routes (без `print()`/`traceback.print_exc()`), удалены bare `except` в `api/openai/transform.py`.
- **Next Step**: Перейти к P1: декомпозиция `chat_completions()` в `api/openai/routes.py` на pipeline-шаги без изменения публичного API-контракта.
- **Blockers**: none
- **Contract Changes**: none
- **Verification**:
  - `uv run python -m compileall api auth core services main.py tests` — success.
  - `uv run python -m unittest discover -s tests -p "test_*.py"` — success (`Ran 18 tests`, `OK`).

## Handoff Notes

### What is done
- Проанализированы ключевые модули:
  - `api/openai/routes.py`
  - `api/gemini/routes.py`
  - `api/parity/routes.py`
  - `services/account_router.py`
  - `services/quota_transport.py`
  - `auth/credentials.py`
  - `auth/qwen_oauth.py`
  - `core/logging.py`
- Выполнены P0-изменения:
  - удалён невалидный импорт `get_user_creds` в `api/openai/routes.py`;
  - заменены `print()`/`traceback.print_exc()` на единый `logger` в `api/openai/routes.py` и `api/gemini/routes.py`;
  - заменены bare `except` на явные исключения в `api/openai/transform.py`.
- Проверена тестовая карта и текущие тесты:
  - `docs/testing/test-map.md`
  - `tests/test_openai_contract.py`
  - `tests/test_quota_account_router.py`
  - `tests/test_quota_429_classification.py`
  - `tests/test_quota_transport_parity.py`
- Верификация после P0: `compileall` и `unittest` успешны (`Ran 18 tests`, `OK`).

### Immediate fix first
- Начать P1: вынести из `chat_completions()` в `api/openai/routes.py` отдельный слой provider strategy (Gemini quota / Qwen quota / Vertex) без изменения внешнего OpenAI-контракта.

### Pending work
1. P1: декомпозиция `chat_completions()` на pipeline-шаги и устранение дублирования stream mapping.
2. P2: расширение тестов для `api/gemini/routes.py` и `api/parity/routes.py`.
3. P2: ревизия `config.py` для минимизации чувствительных defaults в коде.

### Commands to run
- `uv run python -m compileall api auth core services main.py tests`
- `uv run python -m unittest discover -s tests -p "test_*.py"`

### User constraints
- Использовать `uv` как основной инструмент запуска/сборки Python.
- Сохранять quota-first и OpenAI-compatible контракт.
- Не менять требования задачи без явного согласования.

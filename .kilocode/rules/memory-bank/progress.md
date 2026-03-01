# Progress

## История изменений

### 2026-03-01
- Завершена задача [`013-qwen-oauth-multi-account-rotation.md`](tasks_descriptions/tasks/013-qwen-oauth-multi-account-rotation.md): реализован unified quota account-rotation контур для `gemini` и `qwen`.
- Добавлен Qwen OAuth CLI-скрипт [`get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py); зафиксирован scope parity с upstream (`openid profile email model.completion`).
- Добавлены/обновлены тесты ротации и контракта: [`test_quota_account_router.py`](tests/test_quota_account_router.py), [`test_openai_contract.py`](tests/test_openai_contract.py).
- Обновлены test-map/suite и документация: [`docs/testing/test-map.md`](docs/testing/test-map.md), [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md), [`docs/auth.md`](docs/auth.md), [`docs/usage.md`](docs/usage.md), [`.env.example`](.env.example), примеры provider-config в [`docs/examples/`](docs/examples/).
- Верификация: `uv run python -m compileall api auth core services scripts main.py tests` — success; `uv run python -m unittest discover -s tests -p "test_*.py"` — success (`Ran 11 tests`, `OK`).

### 2026-02-28
- Завершена задача [`012-quota-cli-parity-and-kilo-openai-compat.md`](tasks_descriptions/tasks/012-quota-cli-parity-and-kilo-openai-compat.md): стабилизирован quota-first parity контур и обновлены test-map/suite артефакты.
- Обновлён OAuth-скрипт [`get_oauth_credentials.py`](scripts/get_oauth_credentials.py) под поведение, близкое к `gemini-cli`: динамический callback loopback, timeout и ручной fallback авторизации.
- Подтверждено архитектурное решение по прозрачности: для quota-режима не включается скрытый auto-fallback на меньшие модели; при исчерпании емкости сохраняется явный `429 MODEL_CAPACITY_EXHAUSTED`.

### 2026-02-26
- Уточнен приоритет проекта: `quota-first` сценарий как основной продакшен-путь.
- Сформирован и зафиксирован план задачи [`012-quota-cli-parity-and-kilo-openai-compat.md`](tasks_descriptions/tasks/012-quota-cli-parity-and-kilo-openai-compat.md).
- Подтвержден подход верификации parity: runtime capture-relay + статический эталон из кода `gemini-cli`.
- Обновлены Memory Bank артефакты `active.md` и `systemPatterns.md` под новую целевую архитектуру.

### 2026-02-13
- Инициализация Memory Bank.
- Проведен критический анализ кода.
- Выявлены ключевые проблемы: хардкод моделей, небезопасное хранение секретов, отсутствие тестов, неэффективное использование HTTP-клиентов.

# Active Context: Gemini OpenAI Proxy

## Текущая задача
Завершить цикл задачи 013 и зафиксировать unified quota account-rotation для Gemini/Qwen.

## Состояние (чек-лист)
- [x] Завершена задача [`013-qwen-oauth-multi-account-rotation.md`](tasks_descriptions/tasks/013-qwen-oauth-multi-account-rotation.md).
- [x] Добавлен Qwen OAuth CLI-скрипт [`get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py) и зафиксирован рекомендованный scope parity с upstream.
- [x] Добавлены тесты ротации аккаунтов и contract-расширения: [`test_quota_account_router.py`](tests/test_quota_account_router.py), [`test_openai_contract.py`](tests/test_openai_contract.py).
- [x] Обновлены test-map/suite артефакты и документация auth/usage/env.
- [ ] Переключиться на следующую задачу очереди L3.

## Фокус
- Поддерживать прозрачную quota-логику multi-account rotation (`single`/`rounding`) для `gemini` и `qwen`.
- Сохранить OpenAI-compatible stream/non-stream контракт в ротационном контуре.
- Держать документацию и тестовые suite-артефакты в синхронизации с реализацией.

## Next Up (Level 3)
- [009-cli-transport-parity-core.md](tasks_descriptions/tasks/009-cli-transport-parity-core.md)
- [010-gemini-native-routing-and-parity-tests.md](tasks_descriptions/tasks/010-gemini-native-routing-and-parity-tests.md)
- [008-openai-stream-and-contract-tests.md](tasks_descriptions/tasks/008-openai-stream-and-contract-tests.md)
- [011-auth-config-hardening-for-parity.md](tasks_descriptions/tasks/011-auth-config-hardening-for-parity.md)

## Backlog Reference
Смотри директории `tasks_descriptions/tasks/` и `tasks_descriptions/backlog/`.

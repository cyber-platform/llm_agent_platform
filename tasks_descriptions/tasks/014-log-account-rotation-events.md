# Task: Логирование переключения аккаунтов в rounding режиме

## Контекст
- Источник: Запрос пользователя на улучшение observability для quota account rotation
- Связанные артефакты:
  - [`services/account_router.py`](services/account_router.py:1) - реализация unified quota account router
  - [`api/openai/routes.py`](api/openai/routes.py:1) - использование роутера в OpenAI-compatible endpoints
  - [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1) - документация suite для ротации

## Architecture Context References
- [x] [`.kilocode/rules/memory-bank/systemPatterns.md`](.kilocode/rules/memory-bank/systemPatterns.md:1) - паттерн Unified Quota Account Router
- [ ] [`docs/adr/0014-stream-state-container-and-429-rotation-policy.md`](docs/adr/0014-stream-state-container-and-429-rotation-policy.md:1) - ADR для rotation policy

## Specification References
- [ ] [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1) - спецификация поведения ротации

## Test Design References
- [ ] [`tests/test_quota_account_router.py`](tests/test_quota_account_router.py:1) - тесты для account router
- [ ] [`tests/test_openai_contract.py`](tests/test_openai_contract.py:1) - тесты OpenAI contract с ротацией

## Workflow References
- [ ] `none` - workflow не требуется

## Цель
Добавить детальное логирование для переключения аккаунтов в rounding режиме с двумя каналами вывода:
1. **stdout/stderr** - для просмотра в логах Docker контейнера (`docker logs`)
2. **Файлы логов** - для постоянного хранения на смонтированном volume

Логи должны позволять администраторам отслеживать:
1. Когда происходит переключение с одного аккаунта на другой
2. Какой триггер вызвал переключение (RATE_LIMIT или QUOTA_EXHAUSTED)
3. С какого аккаунта на какой произошло переключение
4. Сколько попыток было сделано до переключения

## Шаги реализации

### 1. Настройка двухканального логирования
- [x] Создать модуль `core/logging.py` с настройкой dual-channel logger:
  - [x] Handler для stdout (stderr) - для Docker logs
  - [x] Handler для файловой ротации (RotatingFileHandler) - для persistent логов
  - [x] Форматтер с timestamp, level, module, message
  - [x] Путь к логам: `/app/logs/` внутри контейнера (монтируется как `/data/model_proxy_logs` с хоста)
- [x] Обновить `docker-compose.yml`:
  - [x] Добавить volume `/data/model_proxy_logs:/app/logs:rw` для монтирования папки логов с хоста (HDD)
  - [x] Добавить переменную окружения `LOG_LEVEL` (по умолчанию INFO)
  - [x] Добавить переменную окружения `LOG_DIR` (по умолчанию /app/logs)
- [x] Добавить `logs/` в `.gitignore`

### 2. Логирование в `services/account_router.py`
- [x] Логировать выбор аккаунта в rounding режиме с указанием причины (initial/rotation)
- [x] Логировать переключение аккаунта при превышении threshold ошибок
- [x] Логировать триггер переключения (RATE_LIMIT/QUOTA_EXHAUSTED) и количество накопленных ошибок
- [x] Логировать переход с аккаунта A на аккаунт B

### 3. Логирование в `api/openai/routes.py`
- [x] Логировать запросы (model, stream, usage)
- [x] Логировать переключения при retry

### 4. Обновление тестов
- [x] Все существующие тесты проходят

## Формат логов (реализованный)
```
[provider] rounding: selected account={name} (reason={initial|rotation}|attempt={N}|model={model})
[provider] rounding: rate_limit error for {account} (consecutive={N}/{threshold}|model={model})
[provider] rounding: switching {from} -> {to} (trigger={RATE_LIMIT|QUOTA_EXHAUSTED}|consecutive_errors={N})
[provider] rounding: account {account} exhausted for model {model} (trigger=QUOTA_EXHAUSTED|reset_at={timestamp})
[provider] rounding: account {account} on cooldown (trigger=RATE_LIMIT|duration={seconds}s)
[provider] rounding: all accounts exhausted (trigger={RATE_LIMIT|QUOTA_EXHAUSTED}|model={model})
```

## Definition of Done
- [x] Логирование добавлено в `services/account_router.py` для всех сценариев переключения
- [x] Логирование добавлено в `api/openai/routes.py` для отображения контекста запроса
- [x] Логи содержат: provider, mode, account names, trigger type, error count
- [x] Существующие тесты проходят (18/18 OK)
- [x] Формат логов соответствует предложенному

## Execution Status
- Current State: Задача завершена. Реализовано dual-channel логирование (stdout + файлы на HDD)
- Next Step: Использовать логи для мониторинга ротации аккаунтов в production
- Blockers: none
- Contract Changes: none
- Verification: `uv run python -m unittest discover -s tests -p "test_*.py"` — 18 tests OK

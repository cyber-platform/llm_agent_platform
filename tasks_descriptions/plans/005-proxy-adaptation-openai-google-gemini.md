# Plan: Адаптация прокси под Kilo Code (OpenAI Compatible) и Google Gemini CLI

## Контекст
Цель — доработать **только этот прокси**, чтобы он корректно подстраивался под внешние системы:
- **Kilo Code** как OpenAI-compatible клиент,
- **Google Gemini CLI** как эталон transport/contract поведения в quota-режиме.

Важно: внешние продукты (**Kilo Code** и **Gemini CLI**) не меняем.

## Цели
- Обеспечить стабильную OpenAI-совместимость прокси для Kilo Code/OpenCode.
- Достичь максимально близкого к Gemini CLI поведения запросов к Google в quota-режиме.
- Зафиксировать поведение тестами и конфиг-флагами.

## Границы (Scope)

### In Scope
- [`/v1/chat/completions`](api/openai/routes.py), [`/v1/models`](api/openai/routes.py)
- Native Gemini proxy endpoints в [`api/gemini/routes.py`](api/gemini/routes.py)
- Преобразование OpenAI->Gemini в [`transform_openai_to_gemini()`](api/openai/transform.py:4)
- Конфигурация/аутентификация в [`config.py`](config.py), [`auth/credentials.py`](auth/credentials.py), [`auth/discovery.py`](auth/discovery.py)

### Out of Scope
- Любые изменения в коде Kilo Code и Gemini CLI
- Изменение UX внешних инструментов

## Ключевые разрывы (Gap)

### Для Kilo Code OpenAI-compatible
- Нет корректного приоритета `max_completion_tokens` над `max_tokens` в [`chat_completions()`](api/openai/routes.py:16)
- Принудительный дефолт `maxOutputTokens=65535` в [`chat_completions()`](api/openai/routes.py:36) нарушает ожидаемую модель OpenAI-клиентов
- Несимметричный non-stream контракт в [`chat_completions()`](api/openai/routes.py:330)
- Статический `/v1/models` в [`list_models()`](api/openai/routes.py:455)

### Для parity с Gemini CLI
- Кастомная инъекция `thoughtSignature` bypass в [`transform_openai_to_gemini()`](api/openai/transform.py:4)
- Fallback-цепочка моделей в [`chat_completions()`](api/openai/routes.py:330)
- Зависимость project discovery от env в [`discover_project_id()`](auth/discovery.py:6)

## Целевая архитектура

### 1) Единый transport-слой для Google quota
- Общий модуль вызова Cloud Code endpoint (generate/stream), переиспользуемый в OpenAI и Gemini роутерах.

### 2) Два адаптера на вход/выход
- OpenAI Adapter: преобразование протокола OpenAI к Gemini payload и обратно.
- Gemini Adapter: native passthrough с минимальной нормализацией ошибок.

### 3) Режимы прокси
- `STRICT_CLI_PARITY=true` — отключает fallback/нестандартные обходы.
- `OPENAI_COMPAT_MODE=true` — фиксирует OpenAI-контракт под клиентов.

## План реализации

### Этап A — OpenAI compatibility (MVP)
1. Поддержать `max_completion_tokens` и `max_tokens` (приоритет modern поля)
2. Убрать принудительный дефолт `maxOutputTokens=65535`, если лимит не задан клиентом
3. Унифицировать non-stream OpenAI ответ для quota/vertex
4. Зафиксировать stream usage-chunk при `stream_options.include_usage=true`
5. Сделать `/v1/models` конфигурируемым через env/конфиг

**Результат:** Kilo Code/OpenCode стабильно используют прокси как OpenAI-compatible backend.

### Этап B — Gemini CLI parity (transport/contract)
1. Вынести Cloud Code transport в отдельный модуль и подключить в оба роутера
2. Удалить/отключить bypass-инъекцию `thoughtSignature` в strict parity режиме
3. Отключить fallback chain в strict parity режиме
4. Усилить auth/project discovery и убрать хардкод секретов в конфиге

**Результат:** запросы прокси к Google в quota-режиме максимально близки к Gemini CLI по контракту.

### Этап C — Native Google Gemini профиль в Kilo Code
1. Добавить явный quota routing (не только по суффиксу model id)
2. Поддержать профиль **Google Gemini** с custom base URL на прокси
3. Проверить generate/stream/list models совместимость

**Результат:** доступны оба варианта подключения: OpenAI-compatible и native Google Gemini.

## Стратегия проверки
- Контрактные тесты OpenAI (stream/non-stream/tools/usage/errors)
- Контрактные тесты Gemini native passthrough
- Parity-тесты strict режима (без fallback/инъекций)

## Риски
- Удаление bypass `thoughtSignature` может выявить реальные ограничения некоторых tool-call цепочек
- Отказ от fallback увеличит прозрачность, но уменьшит «магическую» устойчивость
- Миграция auth/config потребует аккуратной обратной совместимости

## Критерии готовности
- [ ] Kilo Code работает через OpenAI-compatible профиль без workaround
- [ ] В strict parity режиме отсутствуют fallback и кастомные инъекции
- [ ] Покрыты тестами stream/non-stream контракты
- [ ] Секреты/креды не захардкожены

## Execution Status
- Current State: план зафиксирован
- Next Step: начать Этап A
- Blockers: none
- Contract Changes: none
- Verification: not started


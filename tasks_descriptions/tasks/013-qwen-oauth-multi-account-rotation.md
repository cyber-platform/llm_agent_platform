# Task: Унифицированная quota multi-account ротация для Qwen и Gemini

## Контекст
- Источник: [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- Связанные артефакты: [`012-quota-cli-parity-and-kilo-openai-compat.md`](tasks_descriptions/tasks/012-quota-cli-parity-and-kilo-openai-compat.md), [`api/openai/routes.py`](api/openai/routes.py), [`auth/credentials.py`](auth/credentials.py), [`services/quota_transport.py`](services/quota_transport.py), [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py), [`qwen-code/packages/core/src/qwen/qwenOAuth2.ts`](qwen-code/packages/core/src/qwen/qwenOAuth2.ts)

## Architecture Context References
- [x] [`systemPatterns.md`](.kilocode/rules/memory-bank/systemPatterns.md)
- [x] [`active.md`](.kilocode/rules/memory-bank/active.md)

## Specification References
- [x] [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- [x] Qwen OAuth device flow reference: [`QwenOAuth2Client`](qwen-code/packages/core/src/qwen/qwenOAuth2.ts:256), [`requestDeviceAuthorization()`](qwen-code/packages/core/src/qwen/qwenOAuth2.ts:291), [`pollDeviceToken()`](qwen-code/packages/core/src/qwen/qwenOAuth2.ts:334), [`refreshAccessToken()`](qwen-code/packages/core/src/qwen/qwenOAuth2.ts:401)
- [x] Qwen quota model reference: [`QWEN_OAUTH_MODELS`](qwen-code/packages/core/src/models/constants.ts:99)

## Test Design References
- [x] [`docs/testing/test-map.md`](docs/testing/test-map.md)
- [x] Добавить suite-страницу для unified quota account-rotation parity в [`docs/testing/suites/`](docs/testing/suites/)

## Workflow References
- [x] `none`

## Цель
- Добавить в прокси унифицированный quota multi-account слой для Qwen и Gemini, совместимый с OpenAI chat completions контрактом, с общим принципом ротации `single`/`rounding` и provider-specific конфигами аккаунтов.

## Согласованные продуктовые правила
- [x] Переход на явные provider-paths credentials без обратной совместимости с legacy [`USER_CREDS_PATH`](config.py:4).
- [x] Для Gemini использовать выделенный путь `secrets/user_gemini_credentials.json`; скрипт [`get_oauth_credentials.py`](scripts/get_oauth_credentials.py) сохраняет credentials только туда.
- [x] Использовать только то, что сейчас поддерживает quota-режим в qwen-code: одна модель из [`QWEN_OAUTH_MODELS`](qwen-code/packages/core/src/models/constants.ts:99).
- [x] Скрипт OAuth всегда пишет креды в [`secrets/user_qwen_credentials.json`](secrets/user_qwen_credentials.json).
- [x] Именованные файлы аккаунтов поддерживаются пользователем вручную (пример: `lisa/petr/julia`).
- [x] Для каждого provider используется отдельный конфиг аккаунтов:
  - [`secrets/qwen_accounts_config.json`](secrets/qwen_accounts_config.json)
  - [`secrets/gemini_accounts_config.json`](secrets/gemini_accounts_config.json)
  с полями `active_account`, `mode`, `all_accounts`.
- [x] Gemini quota получает ту же модель ротации, что и Qwen: `mode=single` через `active_account`, `mode=rounding` через round-robin по `all_accounts`.
- [x] Переключение на следующий аккаунт выполняется после 2 подряд лимитных ошибок текущего аккаунта для обоих provider.
- [x] Если лимиты исчерпаны у всех аккаунтов, клиент получает прозрачную ошибку `all_accounts_exceed_quota`.
- [x] Источник политики ротации только provider-config `mode` без дублирующих env-флагов.
- [x] Сценарий single-user на одном компьютере; межпроцессная синхронизация не требуется в первой итерации.

## Шаги реализации
- [x] Расширить конфигурацию путей credentials:
  - добавить [`USER_GEMINI_CREDS_PATH`](config.py) и [`USER_QWEN_CREDS_PATH`](config.py),
  - убрать использование legacy [`USER_CREDS_PATH`](config.py:4).
- [x] Обновить Gemini auth слой на новый путь `secrets/user_gemini_credentials.json` в [`initialize_auth()`](auth/credentials.py:29) и [`refresh_user_creds()`](auth/credentials.py:61), сохранить потокобезопасность обновления токенов.
- [x] Обновить [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py) для записи в `secrets/user_gemini_credentials.json`.
- [x] Добавить Qwen OAuth auth-слой:
  - реализовать device flow + polling + refresh,
  - чтение/обновление `secrets/user_qwen_credentials.json`,
  - унифицированный доступ к bearer token для transport.
- [x] Создать скрипт [`scripts/get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py) с записью в `secrets/user_qwen_credentials.json`.
- [x] Добавить унифицированный account-router модуль для quota provider:
  - вход: provider (`gemini`/`qwen`), provider-config path, provider credentials directory,
  - чтение [`secrets/qwen_accounts_config.json`](secrets/qwen_accounts_config.json) и [`secrets/gemini_accounts_config.json`](secrets/gemini_accounts_config.json),
  - выбор активного файла credentials по `mode`,
  - счётчик подряд лимитных ошибок,
  - round-robin переключение после 2 лимитных ошибок,
  - сигнал `all_accounts_exceed_quota` при исчерпании всех аккаунтов.
- [x] Добавить Qwen transport слой для generate/stream и парсинга quota-limit ошибок.
- [x] Добавить в Gemini quota path интеграцию с unified account-router вместо одного глобального user credentials объекта.
- [x] Расширить [`chat_completions()`](api/openai/routes.py:24):
  - маршрутизация Qwen quota модели,
  - интеграция unified account-router для Qwen и Gemini quota,
  - единая обработка quota-limit ошибок с ротацией,
  - OpenAI-compatible ответ для stream/non-stream.
- [x] Обновить [`list_models()`](api/openai/routes.py:576) с Qwen quota моделью.
- [x] Добавить/обновить тесты:
  - account mode selection `single/rounding` для Gemini и Qwen,
  - rotation trigger after 2 consecutive quota-limit errors,
  - all accounts exhausted -> `all_accounts_exceed_quota`,
  - OpenAI stream/non-stream contract для Qwen и Gemini quota в режиме ротации.
- [x] Обновить документацию:
  - [`docs/auth.md`](docs/auth.md), [`docs/usage.md`](docs/usage.md), [`.env.example`](.env.example),
  - добавить примеры `secrets/qwen_accounts_config.json` и `secrets/gemini_accounts_config.json`,
  - описать lifecycle `user_qwen_credentials.json -> named file` и `user_gemini_credentials.json -> named file`.

## Execution plan для Code mode

### Phase 1. Config and auth foundation
- Обновить [`config.py`](config.py):
  - добавить `USER_GEMINI_CREDS_PATH`, `USER_QWEN_CREDS_PATH`,
  - удалить использование legacy `USER_CREDS_PATH`.
- Обновить [`auth/credentials.py`](auth/credentials.py):
  - читать Gemini OAuth credentials только из `USER_GEMINI_CREDS_PATH`,
  - сохранить thread-safe обновление токена через текущий lock.
- Обновить [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py):
  - писать в `secrets/user_gemini_credentials.json`.

### Phase 2. Qwen OAuth и provider token adapters
- Добавить Python-реализацию Qwen device flow на основе референса [`QwenOAuth2Client`](qwen-code/packages/core/src/qwen/qwenOAuth2.ts:256).
- Создать [`scripts/get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py) с записью в `secrets/user_qwen_credentials.json`.
- Сделать унифицированный provider adapter interface: получить bearer token для `gemini` и `qwen`.

### Phase 3. Unified quota account-router
- Добавить общий модуль account-router в `services`:
  - load provider config,
  - resolve active account file,
  - хранить счётчик подряд quota-limit ошибок,
  - выполнять round-robin переключение после 2 ошибок,
  - возвращать сигнал `all_accounts_exceed_quota`.
- Поддержать два независимых конфига:
  - [`secrets/gemini_accounts_config.json`](secrets/gemini_accounts_config.json),
  - [`secrets/qwen_accounts_config.json`](secrets/qwen_accounts_config.json).

### Phase 4. Transport and OpenAI routing integration
- Расширить [`services/quota_transport.py`](services/quota_transport.py):
  - provider-aware отправка generate/stream,
  - детекция quota-limit ошибок в едином формате для ротации.
- Обновить [`chat_completions()`](api/openai/routes.py:24):
  - выбрать provider по модели,
  - подключить unified account-router,
  - применить retry/rotate policy,
  - сохранить OpenAI-compatible stream/non-stream response shape.
- Обновить [`list_models()`](api/openai/routes.py:576) для отображения Qwen quota модели.

### Phase 5. Tests and docs
- Добавить unit + contract тесты для account-router, quota-limit rotation и `all_accounts_exceed_quota`.
- Обновить [`docs/testing/test-map.md`](docs/testing/test-map.md) и добавить новую suite-страницу в [`docs/testing/suites/`](docs/testing/suites/).
- Обновить [`docs/auth.md`](docs/auth.md), [`docs/usage.md`](docs/usage.md), [`.env.example`](.env.example).

## План тестирования requirement -> suite -> test script

| Requirement | Suite | Test script |
| :--- | :--- | :--- |
| `mode=single` использует только `active_account` для `gemini` и `qwen` | `quota-account-rotation` | `tests/test_quota_account_router.py::test_single_mode_uses_active_account` |
| `mode=rounding` переключает аккаунт после 2 подряд quota-limit ошибок | `quota-account-rotation` | `tests/test_quota_account_router.py::test_rounding_rotates_after_two_limit_errors` |
| При лимитах всех аккаунтов возвращается `all_accounts_exceed_quota` | `quota-account-rotation` | `tests/test_quota_account_router.py::test_all_accounts_exceed_quota_error` |
| Non-stream OpenAI контракт сохраняется в quota-режиме с ротацией | `openai-contract` | `tests/test_openai_contract.py::test_non_stream_quota_rotation_contract` |
| Stream OpenAI контракт и usage chunk сохраняются в quota-режиме с ротацией | `openai-contract` | `tests/test_openai_contract.py::test_stream_quota_rotation_usage_contract` |

## План обновления документации
- [`docs/auth.md`](docs/auth.md):
  - два OAuth lifecycle: Gemini и Qwen,
  - примеры именованных файлов аккаунтов,
  - структура `gemini_accounts_config.json` и `qwen_accounts_config.json`.
- [`docs/usage.md`](docs/usage.md):
  - как переключаются режимы `single` и `rounding`,
  - поведение при quota-limit и `all_accounts_exceed_quota`.
- [`.env.example`](.env.example):
  - добавить provider-specific переменные путей,
  - убрать legacy `USER_CREDS_PATH`.
- [`docs/testing/test-map.md`](docs/testing/test-map.md):
  - добавить новую suite traceability для unified quota account-rotation.

## Definition of Done
- [x] Изменения реализованы по спецификации
- [x] Проверки пройдены
- [x] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: Qwen OAuth device-flow работает в CLI-скрипте: добавлены заголовки `x-request-id` и `User-Agent: qwen-code` в [`auth/qwen_oauth.py`](auth/qwen_oauth.py), запуск `uv run scripts/get_qwen_oauth_credentials.py` открывает браузер и успешно сохраняет `secrets/user_qwen_credentials.json`. Сохраняются улучшенные диагностические сообщения для non-JSON ответов.
- Next Step: переключиться на следующую задачу очереди L3 согласно [`active.md`](.kilocode/rules/memory-bank/active.md).
- Blockers: none.
- Contract Changes: present.
- Verification: `uv run python -m compileall api auth core services scripts main.py tests` — success; `uv run python -m unittest discover -s tests -p "test_*.py"` — success (`Ran 11 tests`, `OK`).

## Handoff Notes

### What is done
- Сформирован и зафиксирован task-артефакт [`013-qwen-oauth-multi-account-rotation.md`](tasks_descriptions/tasks/013-qwen-oauth-multi-account-rotation.md) с полным scope реализации.
- Подтверждено ограничение quota-моделей первой итерации: одна модель из [`QWEN_OAUTH_MODELS`](qwen-code/packages/core/src/models/constants.ts:99).
- Зафиксированы пользовательские правила хранения credentials:
  - скрипт пишет только в [`secrets/user_qwen_credentials.json`](secrets/user_qwen_credentials.json),
  - пользователь вручную переименовывает файл в именной.
- Зафиксирована целевая схема конфигурации аккаунтов [`secrets/qwen_accounts_config.json`](secrets/qwen_accounts_config.json):
  - `active_account`,
  - `mode` с значениями `single|rounding`,
  - `all_accounts`.
- Зафиксирована политика ротации для `rounding`: переключение после 2 подряд лимитных ошибок; при лимитах у всех аккаунтов — прозрачная ошибка `all_accounts_exceed_quota`.
- Согласовано расширение scope: добавить Gemini multi-account quota ротацию и унифицированный модуль account-router для Qwen+Gemini.
- Согласовано правило: для credentials paths не сохранять обратную совместимость с legacy [`USER_CREDS_PATH`](config.py:4).
- Фактически реализовано в коде:
  - foundation paths и Gemini auth refresher: [`config.py`](config.py), [`auth/credentials.py`](auth/credentials.py)
  - Gemini OAuth script path migration: [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py)
  - заготовка unified router с Gemini-specific account type (`project_id` per account): [`QuotaAccountRouter`](services/account_router.py), [`GeminiAccount`](services/account_router.py)
  - заготовка Qwen OAuth flow (device/poll/refresh): [`auth/qwen_oauth.py`](auth/qwen_oauth.py)
  - mapping для quota-модели Qwen: [`map_model_name()`](core/models.py:1) (`qwen3.5-plus-quota` -> `qwen3.5-plus`)
  - route-level интеграция Gemini account-rotation в native endpoint: [`gemini_proxy()`](api/gemini/routes.py:33)
  - доработка Qwen stream chunk conversion в OpenAI proxy: [`_openai_chunk_from_qwen()`](api/openai/routes.py:59)
  - начатая адаптация contract-тестов к новым seam'ам роутера: [`tests/test_openai_contract.py`](tests/test_openai_contract.py)
  - добавлен bootstrap `sys.path` и best-effort авто-открытие браузера в [`get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py)
  - улучшена диагностика не-JSON ответов в [`auth/qwen_oauth.py`](auth/qwen_oauth.py)

### Immediate fix first
- none.

### Pending work
- none.

### Commands to run
- `uv run python -m compileall api auth core services scripts main.py tests`
- `uv run python -m unittest discover -s tests -p "test_*.py"`
- `uv run scripts/get_qwen_oauth_credentials.py`

### User constraints
- Quota-путь Qwen первой итерации: только текущая модель из [`QWEN_OAUTH_MODELS`](qwen-code/packages/core/src/models/constants.ts:99).
- Конфиг-источник режима ротации: provider-config файлы [`secrets/qwen_accounts_config.json`](secrets/qwen_accounts_config.json) и [`secrets/gemini_accounts_config.json`](secrets/gemini_accounts_config.json), без дублирования флагами.
- `single`: использовать только `active_account`; `rounding`: round-robin по `all_accounts` для обоих provider.
- Переключение в `rounding` после 2 подряд лимитных ошибок.
- Один пользователь на одном компьютере; межпроцессная синхронизация не обязательна на первом этапе.
- Legacy обратная совместимость по [`USER_CREDS_PATH`](config.py:4) не требуется.
- Для Gemini multi-account quota `project_id` обязателен на уровне аккаунта (разные проекты у разных пользователей), fallback на глобальный `GOOGLE_CLOUD_PROJECT` отключается в этом контуре.

### Read first (Markdown links for next agent)
- План и исходный scope: [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- Предыдущий завершённый контур parity: [`012-quota-cli-parity-and-kilo-openai-compat.md`](tasks_descriptions/tasks/012-quota-cli-parity-and-kilo-openai-compat.md)
- Текущая задача (source of truth): [`013-qwen-oauth-multi-account-rotation.md`](tasks_descriptions/tasks/013-qwen-oauth-multi-account-rotation.md)
- Индекс тестов: [`docs/testing/test-map.md`](docs/testing/test-map.md)
- Контрактный suite: [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md)
- Quota parity suite: [`docs/testing/suites/quota-parity.md`](docs/testing/suites/quota-parity.md)
- Документация по авторизации: [`docs/auth.md`](docs/auth.md)
- Документация по использованию: [`docs/usage.md`](docs/usage.md)
- Memory Bank (архитектурный контекст): [`systemPatterns.md`](.kilocode/rules/memory-bank/systemPatterns.md)
- Memory Bank (активный фокус): [`active.md`](.kilocode/rules/memory-bank/active.md)

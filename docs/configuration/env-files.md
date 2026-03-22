# Env configuration: `.env` и `.env.oauth`

Связанные решения:

- [`ADR 0015`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1)

## 1) Контуры и ответственность

### 1.1 Runtime (контейнер прокси)

Runtime переменные — это все ключи, которые используются процессом прокси во время работы контейнера.

Источники:

- [`.env`](.env:1) — storage значений runtime.
- [`docker-compose.yml`](docker-compose.yml:1) — **единственный** механизм инъекции runtime env в контейнер.

Политика:

- Все runtime ключи должны попадать в контейнер **явно** через [`docker-compose.yml`](docker-compose.yml:1).
- Runtime ключи должны быть задокументированы и перечислены в [`.env.example`](.env.example:1).

### 1.2 OAuth bootstrap (локальные скрипты)

Bootstrap переменные — ключи, которые нужны только для одноразового получения/обновления OAuth credentials локальными скриптами.

Источники:

- [`.env.oauth`](.env.oauth:1) — storage значений bootstrap (создается пользователем локально, не коммитится).
- Локальные скрипты должны загружать [`.env`](.env:1) и [`.env.oauth`](.env.oauth:1) **до** импорта [`llm_agent_platform/config.py`](llm_agent_platform/config.py:1).

Политика:

- Bootstrap ключи не должны автоматически попадать в контейнер.
- Bootstrap ключи должны быть задокументированы в [`.env.oauth.example`](.env.oauth.example:1).

## 2) Порядок загрузки для локальных скриптов

Нормативный порядок загрузки для локальных скриптов:

1) загрузить [`.env`](.env:1)
2) загрузить [`.env.oauth`](.env.oauth:1) с override (bootstrap перекрывает runtime при необходимости)
3) импортировать [`llm_agent_platform/config.py`](llm_agent_platform/config.py:1) и использовать значения из `os.environ`

Цели:

- избежать ручного `export` при запуске из VS Code/uv;
- гарантировать единый механизм конфигурации для обоих OAuth скриптов.

Скрипты, которые должны следовать этому правилу:

- [`scripts/get_gemini-cli_credentials.py`](scripts/get_gemini-cli_credentials.py:1)
- [`scripts/get_qwen-code_credentials.py`](scripts/get_qwen-code_credentials.py:1)
- [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py:1)

## 3) Инъекция runtime env в контейнер

Контейнер должен получать переменные окружения **явно** через [`docker-compose.yml`](docker-compose.yml:1).

Требование прозрачности:

- если ключ используется в коде (см. [`llm_agent_platform/config.py`](llm_agent_platform/config.py:1) и прямые `os.environ.get` вызовы в runtime), он должен быть перечислен в `environment:` compose-файла.
- `env_file` допускается только как storage значений, но не заменяет перечисление ключей.

## 4) Канонический список переменных (source-of-truth)

Источник истины по используемым переменным — код:

- ключи в [`llm_agent_platform/config.py`](llm_agent_platform/config.py:1)
- прямые обращения к `os.environ` в runtime коде, если такие остаются как технический долг

### Дополнение: provider-scoped secrets layout (Proposed)
Рекомендуемая структура `secrets/<provider_id>/...` описана в:
- [`docs/architecture/quota-reset-periods-and-account-state.md`](docs/architecture/quota-reset-periods-and-account-state.md:1)

Runtime env ключ для Qwen idle refresh:
- `QWEN_REFRESH_IDLE_THRESHOLD_SECONDS` (default: `180`)

Для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) runtime использует:
- `USER_OPENAI_CHATGPT_CREDS_PATH` — persisted OAuth state path;
- `OPENAI_CHATGPT_ACCOUNTS_CONFIG_PATH` — provider accounts-config с режимом `single` или `rounding`;
- `OPENAI_CHATGPT_BACKEND_BASE_URL` и `OPENAI_CHATGPT_RESPONSES_PATH` — private backend surface;
- `OPENAI_CHATGPT_USAGE_URL` — monitoring-only usage adapter;
- `OPENAI_CHATGPT_REFRESH_BUFFER_SECONDS` — preemptive refresh buffer для runtime OAuth manager.

Текущие canonical defaults для provider-scoped accounts configs:
- `GEMINI_ACCOUNTS_CONFIG_PATH=secrets/gemini-cli/accounts_config.json`
- `QWEN_ACCOUNTS_CONFIG_PATH=secrets/qwen_code/accounts_config.json`
- `OPENAI_CHATGPT_ACCOUNTS_CONFIG_PATH=secrets/openai-chatgpt/accounts_config.json`

Bootstrap script [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py:1) использует локальные OAuth env:
- `OPENAI_CHATGPT_OAUTH_CLIENT_ID`
- `OPENAI_CHATGPT_OAUTH_SCOPE`
- `OPENAI_CHATGPT_OAUTH_AUTHORIZE_ENDPOINT`
- `OPENAI_CHATGPT_OAUTH_TOKEN_ENDPOINT`
- `OPENAI_CHATGPT_OAUTH_CALLBACK_HOST`
- `OPENAI_CHATGPT_OAUTH_CALLBACK_PORT`
- `OPENAI_CHATGPT_OAUTH_CALLBACK_PATH`

### Дополнение: state persistence на HDD (Proposed)

Для quota state persistence вводятся новые runtime env ключи:

- `STATE_DIR` — директория, где храним state-файлы (`account_state.json`, group snapshot `quota_state.json`); optional, code default `/app/state`.
- `STATE_FLUSH_INTERVAL_SECONDS` — период flush async writer на диск; optional, default `3`.
- `STATE_WRITER_MAX_PENDING_FILES` — лимит уникальных путей в coalesce map; optional, default `1024`.

Канонический документ:

- [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)

Политика runtime defaults:

- `STATE_DIR` может иметь code default, но в container deployments должен быть перечислен явно в [`docker-compose.yml`](docker-compose.yml:1), чтобы storage layout был прозрачен.
- для локальной разработки рекомендуется override на HDD-backed путь, если это важно для wear-leveling;
- `STATE_FLUSH_INTERVAL_SECONDS` должен быть `> 0`;
- `STATE_WRITER_MAX_PENDING_FILES` должен быть `>= 1`;
- при overflow writer применяет `drop-oldest` и пишет warning в лог;
- при graceful shutdown writer делает best-effort final flush; crash-safe гарантии beyond last successful flush не даются.

Дальнейшая реализация должна привести к состоянию, где:

- runtime переменные читаются централизованно через конфиг-слой (а не через разбросанные `os.environ.get`),
- неиспользуемые ключи удалены из [`.env.example`](.env.example:1),
- обязательные ключи валидируются при старте.

## 5) Policy: no hidden defaults

Если runtime поведение зависит от значения ключа, то скрытые значения по умолчанию в коде считаются нежелательными.

Нормативное требование:

- runtime ключи либо обязательны (fail-fast при старте),
- либо явно помечены как optional и описано поведение при отсутствии.

Ссылки:

- политика зафиксирована в [`ADR 0015`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1) и в этом документе.

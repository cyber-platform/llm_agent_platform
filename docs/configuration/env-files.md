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
- Локальные скрипты должны загружать [`.env`](.env:1) и [`.env.oauth`](.env.oauth:1) **до** импорта [`config.py`](config.py:1).

Политика:

- Bootstrap ключи не должны автоматически попадать в контейнер.
- Bootstrap ключи должны быть задокументированы в [`.env.oauth.example`](.env.oauth.example:1).

## 2) Порядок загрузки для локальных скриптов

Нормативный порядок загрузки для локальных скриптов:

1) загрузить [`.env`](.env:1)
2) загрузить [`.env.oauth`](.env.oauth:1) с override (bootstrap перекрывает runtime при необходимости)
3) импортировать [`config.py`](config.py:1) и использовать значения из `os.environ`

Цели:

- избежать ручного `export` при запуске из VS Code/uv;
- гарантировать единый механизм конфигурации для обоих OAuth скриптов.

Скрипты, которые должны следовать этому правилу:

- [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py:1)
- [`scripts/get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py:1)

## 3) Инъекция runtime env в контейнер

Контейнер должен получать переменные окружения **явно** через [`docker-compose.yml`](docker-compose.yml:1).

Требование прозрачности:

- если ключ используется в коде (см. [`config.py`](config.py:1) и прямые `os.environ.get` вызовы в runtime), он должен быть перечислен в `environment:` compose-файла.
- `env_file` допускается только как storage значений, но не заменяет перечисление ключей.

## 4) Канонический список переменных (source-of-truth)

Источник истины по используемым переменным — код:

- ключи в [`config.py`](config.py:1)
- прямые обращения к `os.environ` в runtime коде (например [`services/http_pool.py`](services/http_pool.py:1), [`api/openai/routes.py`](api/openai/routes.py:1))

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

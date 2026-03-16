# Suite: Config env split + repo layout refactor

## Scope

Этот suite фиксирует тест-дизайн для двух связанных изменений:

1) Разделение runtime env и OAuth bootstrap env.
2) Перенос нашего кода в `src/` с оформлением runtime как пакета.

Связанные артефакты:

- [`ADR 0015`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1)
- [`ADR 0016`](docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md:1)
- Политика env: [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)
- Runtime инъекция env: [`docker-compose.yml`](docker-compose.yml:1)

## Requirement Traceability

### Env split

- Локальные OAuth скрипты **должны** загружать [`.env`](.env:1) и [`.env.oauth`](.env.oauth:1) до импорта [`config.py`](config.py:1).
- Bootstrap ключи **не должны** попадать в контейнер автоматически.
- Runtime ключи **должны** инъектироваться **явно** через [`docker-compose.yml`](docker-compose.yml:1) и быть задокументированы в [`.env.example`](.env.example:1).

### Repo layout

- Целевое состояние:
  - runtime приложение оформлено как модуль и запускается через `uv run python -m model_proxy`.
  - runtime код расположен в `src/model_proxy/`, локальные скрипты — в `src/scripts/`.
  - после переноса в `src/` тесты продолжают проходить.

## Test Cases (Given / When / Then)

### TC-001 (L2): Local Gemini OAuth script loads `.env` + `.env.oauth`

Given:
- существует [`.env`](.env:1)
- существует [`.env.oauth`](.env.oauth:1) с ключами для [`GEMINI_CLI_CLIENT_ID`](config.py:40) и [`GEMINI_CLI_CLIENT_SECRET`](config.py:41)

When:
- запускаем локально `uv run python src/scripts/get_oauth_credentials.py`

Then:
- скрипт не падает на проверках `client_id/client_secret`
- создается `secrets/user_gemini_credentials.json`

### TC-002 (L2): Local Qwen OAuth script loads `.env` + `.env.oauth`

Given:
- существует [`.env.oauth`](.env.oauth:1) с ключом для [`QWEN_OAUTH_CLIENT_ID`](config.py:50)

When:
- запускаем локально `uv run python src/scripts/get_qwen_oauth_credentials.py`

Then:
- скрипт не падает на проверке client_id в [`auth/qwen_oauth.py`](auth/qwen_oauth.py:30)

### TC-003 (L2): Container runtime env injection is explicit

Given:
- runtime значения заданы в [`.env`](.env:1)
- [`docker-compose.yml`](docker-compose.yml:1) перечисляет все runtime ключи в `environment:`

When:
- запускаем `docker compose up` и поднимаем контейнер

Then:
- внутри контейнера доступны все runtime ключи
- прокси стартует и отдает `/v1/models`

### TC-004 (L1/L2): No unused env keys

Given:
- runtime ключи перечислены в [`.env.example`](.env.example:1)

When:
- статически анализируем код на обращения к env (например через grep/линтер)

Then:
- каждый ключ из [`.env.example`](.env.example:1) используется в коде, или явно помечен optional и задокументирован

### TC-101 (L2): Entrypoint runs as module

Given:
- код прокси перенесен в `src/model_proxy/`

When:
- запускаем `uv run python -m model_proxy`

Then:
- приложение поднимается и регистрирует blueprints

### TC-102 (L2): Unit tests still pass after refactor

Given:
- перенос в `src/` завершен

When:
- запускаем `uv run python -m unittest discover -s tests -p test_*.py`

Then:
- тесты проходят

## Coverage Matrix

| Requirement | Test Case | Level |
|---|---|---|
| US-001 | TC-001 | L2 |
| US-002 | TC-002 | L2 |
| US-003 | TC-003 | L2 |
| NFR-001 | TC-003 | L2 |
| NFR-003 | TC-001, TC-002 | L2 |
| US-102 | TC-101, TC-003 | L2 |
| NFR-101 | TC-102 | L2 |

## Verification Command

Команды верификации должны быть уточнены и зафиксированы в task-артефактах реализации.

# Suite: Config env split + runtime package layout

## Scope

Этот suite фиксирует тестовый контур для двух связанных архитектурных инвариантов:

1) Разделение runtime env и OAuth bootstrap env.
2) Явный layout с runtime package в [`llm_agent_platform/`](llm_agent_platform:1) и local scripts в [`scripts/`](scripts:1).

Связанные артефакты:

- [`docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1)
- [`docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md`](docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md:1)
- Политика env: [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)
- Runtime инъекция env: [`docker-compose.yml`](docker-compose.yml:1)

## Requirement Traceability

### Env split

- Локальные OAuth скрипты **должны** загружать [`.env`](.env:1) и [`.env.oauth`](.env.oauth:1) до импорта [`llm_agent_platform/config.py`](llm_agent_platform/config.py:1).
- Bootstrap ключи **не должны** попадать в контейнер автоматически.
- Runtime ключи **должны** инъектироваться **явно** через [`docker-compose.yml`](docker-compose.yml:1) и быть задокументированы в [`.env.example`](.env.example:1).

### Repo layout

- Целевое и текущее canonical состояние:
  - runtime приложение оформлено как пакет [`llm_agent_platform/`](llm_agent_platform:1) и запускается через [`llm_agent_platform/__main__.py`](llm_agent_platform/__main__.py:1);
  - runtime код расположен в [`llm_agent_platform/`](llm_agent_platform:1), локальные скрипты — в [`scripts/`](scripts:1);
  - документация, команды запуска и smoke verification должны ссылаться на фактический layout проекта.

## Test Cases (Given / When / Then)

### TC-001 (L2): Local Gemini OAuth script loads `.env` + `.env.oauth`

Given:
- существует [`.env`](.env:1)
- существует [`.env.oauth`](.env.oauth:1) с ключами для [`Config.GEMINI_CLI_CLIENT_ID`](llm_agent_platform/config.py:50) и [`Config.GEMINI_CLI_CLIENT_SECRET`](llm_agent_platform/config.py:51)

When:
- запускаем локально `uv run python scripts/get_gemini-cli_credentials.py`

Then:
- скрипт не падает на проверках `client_id/client_secret`
- создается `secrets/gemini-cli/user_credentials.json`

### TC-002 (L2): Local Qwen OAuth script loads `.env` + `.env.oauth`

Given:
- существует [`.env.oauth`](.env.oauth:1) с ключом для [`Config.QWEN_OAUTH_CLIENT_ID`](llm_agent_platform/config.py:60)

When:
- запускаем локально `uv run python scripts/get_qwen-code_credentials.py`

Then:
- скрипт не падает на проверке client_id в [`llm_agent_platform/auth/qwen_oauth.py`](llm_agent_platform/auth/qwen_oauth.py:26)

### TC-003 (L2): Container runtime env injection is explicit

Given:
- runtime значения заданы в [`.env`](.env:1)
- [`docker-compose.yml`](docker-compose.yml:1) перечисляет все runtime ключи в `environment:`

When:
- запускаем `docker compose up` и поднимаем контейнер

Then:
- внутри контейнера доступны все runtime ключи
- прокси стартует и отдает provider-scoped `/models`

### TC-004 (L1/L2): No unused env keys

Given:
- runtime ключи перечислены в [`.env.example`](.env.example:1)

When:
- статически анализируем код на обращения к env (например через grep/линтер)

Then:
- каждый ключ из [`.env.example`](.env.example:1) используется в коде, или явно помечен optional и задокументирован

### TC-101 (L2): Entrypoint runs via runtime package

Given:
- runtime package расположен в [`llm_agent_platform/`](llm_agent_platform:1)

When:
- запускаем `uv run python -m llm_agent_platform`

Then:
- приложение поднимается и регистрирует blueprints

### TC-102 (L2): Unit tests still pass with current layout

Given:
- runtime использует текущий package layout [`llm_agent_platform/`](llm_agent_platform:1)

When:
- запускаем `uv run python -m unittest discover -s llm_agent_platform/tests -p "test_*.py"`

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

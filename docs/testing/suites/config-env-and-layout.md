# Suite: Config env split + runtime package layout

## Suite ID
- `TS-CONFIG-ENV-AND-LAYOUT`

## Documentation roots
- `docs/testing/test-map.md`
- `docs/testing/traceability.md`
- `docs/testing/suites/config-env-and-layout.md`

## Implementation roots
- `services/backend/llm_agent_platform/tests/`
- `services/backend/scripts/`
- `docker-compose.yml`

## Search anchors
- `TS-CONFIG-ENV-AND-LAYOUT`
- `TC-CONFIG-ENV-AND-LAYOUT-`
- `.env.oauth`
- `services/backend/llm_agent_platform/__main__.py`

## Scope

Этот suite фиксирует тестовый контур для двух связанных архитектурных инвариантов:

1) Разделение runtime env и OAuth bootstrap env.
2) Явный layout с runtime package в [`services/backend/llm_agent_platform/`](services/backend/llm_agent_platform:1) и local scripts в [`services/backend/scripts/`](services/backend/scripts:1).

Связанные артефакты:

- [`docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1)
- [`docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md`](docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md:1)
- Политика env: [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)
- Runtime инъекция env: [`docker-compose.yml`](docker-compose.yml:1)

## Requirement Traceability

- Suite rollout note: suite-level anchor уже каноничен как `TS-CONFIG-ENV-AND-LAYOUT`; this suite also uses normalized `TC-CONFIG-ENV-AND-LAYOUT-*` identifiers as baseline for future test metadata rollout.

### Env split

- Локальные OAuth скрипты **должны** загружать [`.env`](.env:1) и [`.env.oauth`](.env.oauth:1) до импорта [`services/backend/llm_agent_platform/config.py`](services/backend/llm_agent_platform/config.py:1).
- Bootstrap ключи **не должны** попадать в контейнер автоматически.
- Runtime ключи **должны** инъектироваться **явно** через [`docker-compose.yml`](docker-compose.yml:1) и быть задокументированы в [`services/backend/.env.example`](services/backend/.env.example:1).

### Repo layout

- Целевое и текущее canonical состояние:
  - runtime приложение оформлено как пакет [`services/backend/llm_agent_platform/`](services/backend/llm_agent_platform:1) и запускается через [`services/backend/llm_agent_platform/__main__.py`](services/backend/llm_agent_platform/__main__.py:1);
  - runtime код расположен в [`services/backend/llm_agent_platform/`](services/backend/llm_agent_platform:1), локальные скрипты — в [`services/backend/scripts/`](services/backend/scripts:1);
  - документация, команды запуска и smoke verification должны ссылаться на фактический layout проекта.

## Test Cases (Given / When / Then)

### TC-CONFIG-ENV-AND-LAYOUT-001 (L2): Local Gemini OAuth script loads `.env` + `.env.oauth`

Given:
- существует [`.env`](.env:1)
- существует [`.env.oauth`](.env.oauth:1) с ключами для [`Config.GEMINI_CLI_CLIENT_ID`](services/backend/llm_agent_platform/config.py:50) и [`Config.GEMINI_CLI_CLIENT_SECRET`](services/backend/llm_agent_platform/config.py:51)

When:
- запускаем локально `uv run --project services/backend python services/backend/scripts/get_gemini-cli_credentials.py`

Then:
- скрипт не падает на проверках `client_id/client_secret`
- создается `secrets/gemini-cli/user_credentials.json`

### TC-CONFIG-ENV-AND-LAYOUT-002 (L2): Local Qwen OAuth script loads `.env` + `.env.oauth`

Given:
- существует [`.env.oauth`](.env.oauth:1) с ключом для [`Config.QWEN_OAUTH_CLIENT_ID`](services/backend/llm_agent_platform/config.py:60)

When:
- запускаем локально `uv run --project services/backend python services/backend/scripts/get_qwen-code_credentials.py`

Then:
- скрипт не падает на проверке client_id в [`services/backend/llm_agent_platform/auth/qwen_oauth.py`](services/backend/llm_agent_platform/auth/qwen_oauth.py:26)

### TC-CONFIG-ENV-AND-LAYOUT-003 (L2): Container runtime env injection is explicit

Given:
- runtime значения заданы в [`.env`](.env:1)
- [`docker-compose.yml`](docker-compose.yml:1) перечисляет все runtime ключи в `environment:`

When:
- запускаем `docker compose up` и поднимаем контейнер

Then:
- внутри контейнера доступны все runtime ключи
- прокси стартует и отдает provider-scoped `/models`

### TC-CONFIG-ENV-AND-LAYOUT-004 (L1/L2): No unused env keys

Given:
- runtime ключи перечислены в [`services/backend/.env.example`](services/backend/.env.example:1)

When:
- статически анализируем код на обращения к env (например через grep/линтер)

Then:
- каждый ключ из [`services/backend/.env.example`](services/backend/.env.example:1) используется в коде, или явно помечен optional и задокументирован

### TC-CONFIG-ENV-AND-LAYOUT-101 (L2): Entrypoint runs via runtime package

Given:
- runtime package расположен в [`services/backend/llm_agent_platform/`](services/backend/llm_agent_platform:1)

When:
- запускаем `uv run --project services/backend python -m llm_agent_platform`

Then:
- приложение поднимается и регистрирует blueprints

### TC-CONFIG-ENV-AND-LAYOUT-102 (L2): Unit tests still pass with current layout

Given:
- runtime использует текущий package layout [`services/backend/llm_agent_platform/`](services/backend/llm_agent_platform:1)

When:
- запускаем `cd services/backend && uv run python -m unittest discover -s llm_agent_platform/tests -p "test_*.py"`

Then:
- тесты проходят

## Coverage Matrix

| Requirement | Test Case | Level |
|---|---|---|
| US-001 | TC-CONFIG-ENV-AND-LAYOUT-001 | L2 |
| US-002 | TC-CONFIG-ENV-AND-LAYOUT-002 | L2 |
| US-003 | TC-CONFIG-ENV-AND-LAYOUT-003 | L2 |
| NFR-001 | TC-CONFIG-ENV-AND-LAYOUT-003 | L2 |
| NFR-003 | TC-CONFIG-ENV-AND-LAYOUT-001, TC-CONFIG-ENV-AND-LAYOUT-002 | L2 |
| US-102 | TC-CONFIG-ENV-AND-LAYOUT-101, TC-CONFIG-ENV-AND-LAYOUT-003 | L2 |
| NFR-101 | TC-CONFIG-ENV-AND-LAYOUT-102 | L2 |

## Verification Command

Команды верификации должны быть уточнены и зафиксированы в task-артефактах реализации.

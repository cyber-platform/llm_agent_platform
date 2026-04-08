# Spec: Разделение runtime и OAuth bootstrap env

Связанное архитектурное решение: [`ADR 0015`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1).

## 1) Problem and goals

### Problem
Локальные OAuth-скрипты (вне контейнера) не видят переменные из [`.env`](.env:1), потому что [`config.py`](config.py:1) читает только `os.environ` (см. [`_env_str`](config.py:4)). Это приводит к ошибкам при запуске из VS Code/uv, например в [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py:99).

Дополнительно, [`.env.example`](.env.example:1) смешивает переменные разных контуров (runtime прокси и OAuth bootstrap), что размывает границы ответственности.

### Goals
- **G-1**: Локальные OAuth-скрипты подхватывают конфиг детерминированно без ручного `export`.
- **G-2**: Контейнер прокси получает runtime-переменные детерминированно.
- **G-3**: OAuth bootstrap секреты не попадают в контейнер автоматически.
- **G-4**: Документация и примеры env-файлов отражают разделение ответственности.

## 2) Non-goals
- Не меняем формат файлов credentials в `secrets/`.
- Не меняем логику ротации аккаунтов и quota-политики.
- Не вводим новый внешний сервис конфигурации.

## 3) Use cases / User stories

- **US-001**: Разработчик запускает [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py:1) в VS Code и получает `secrets/user_gemini_credentials.json` без ручного экспорта env.
  - AC: проверка наличия [`GEMINI_CLI_CLIENT_ID`](config.py:40) проходит.

- **US-002**: Разработчик запускает [`scripts/get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py:1) в VS Code и получает `secrets/user_qwen_credentials.json` без ручного экспорта env.
  - AC: проверка наличия [`QWEN_OAUTH_CLIENT_ID`](config.py:50) проходит (через [`auth/qwen_oauth.py`](auth/qwen_oauth.py:1)).

- **US-003**: Оператор запускает контейнер прокси через [`docker-compose.yml`](docker-compose.yml:1) и runtime-переменные применяются в контейнере.
  - AC: процесс прокси читает env через [`config.py`](config.py:1), а `secrets/` доступна через volume (см. [`docker-compose.yml`](docker-compose.yml:11)).

## 4) NFR

- **NFR-001 Security**: OAuth bootstrap секреты (например, [`GEMINI_CLI_CLIENT_SECRET`](config.py:41)) не должны автоматически попадать в окружение контейнера.
- **NFR-002 DX**: Команды запуска OAuth скриптов из VS Code/uv не требуют ручного `source`.
- **NFR-003 Determinism**: Приоритет загрузки конфигов фиксирован: `.env` затем `.env.oauth`.

## 5) Constraints

- **CONS-001**: [`.env`](.env:1) не копируется в docker image (см. игнор в [`.dockerignore`](.dockerignore:3)).
- **CONS-002**: Данные токенов хранятся только в `secrets/` и монтируются в контейнер (см. [`docker-compose.yml`](docker-compose.yml:11)).
- **CONS-003**: Новые файлы с секретами не коммитятся (нужно обновление `.gitignore`).

## 6) Architecture overview (components and boundaries)

### Компоненты

1) **Local OAuth Bootstrap**
   - Скрипты: [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py:1), [`scripts/get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py:1)
   - Источники конфигурации: [`.env`](.env:1) + [`.env.oauth`](.env.oauth:1)
   - Output: файлы credentials в `secrets/`

2) **Proxy Runtime (Container)**
   - Вход конфигурации: runtime env через `env_file` в [`docker-compose.yml`](docker-compose.yml:1)
   - Вход auth данных: volume `./secrets:/app/secrets` в [`docker-compose.yml`](docker-compose.yml:11)
   - Внутренний интерфейс конфигурации: [`config.py`](config.py:1)

### Границы
- `.env.oauth` — **только** локальный bootstrap, не используется контейнером.
- `secrets/` — единый канал передачи credentials внутрь контейнера.

## 7) Domain model

Минимальная доменная модель для этой фичи — «источники конфигурации»:

- **RuntimeEnv**: набор ключей, влияющих на поведение прокси.
- **BootstrapEnv**: набор ключей, необходимых для одноразового получения credentials.
- **ProcessEnv**: эффективные переменные окружения процесса (после загрузки файлов).
- **SecretsVolume**: файлы credentials, доступные контейнеру.

## 8) Key models

- Конфиг-модуль: [`config.py`](config.py:1)
- Пример runtime env: [`.env.example`](.env.example:1)
- Пример bootstrap env: [`.env.oauth.example`](.env.oauth.example:1)

## 9) Contracts

Внешних API контрактов не добавляется. Изменения ограничены конфигурацией запуска.

## 10) Test design

Канонический тест-дизайн для реализации должен быть оформлен отдельным документом и привязан к этой спецификации.

## 11) Coverage matrix

| Requirement | Test Case | Level |
|---|---|---|
| US-001 | TC-001 | L4 (manual) + L2 (script smoke) |
| US-002 | TC-002 | L4 (manual) + L2 (script smoke) |
| US-003 | TC-003 | L2 (compose run) |
| NFR-001 | TC-004 | L2 (inspect effective env in container) |
| NFR-003 | TC-005 | L1/L2 (load order) |

## 12) Risk register

| Risk ID | Risk statement | Category | Prob | Impact | Detection | Mitigation | Contingency | Owner | Status | Links |
|---|---|---|---|---|---|---|---|---|---|---|
| R-001 | `.env.oauth` случайно попадет в git | Security | M | H | `git status` показывает файл | Добавить в `.gitignore`, документировать | Вынести секреты в другой storage | Maintainer | Open | [`ADR 0015`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1) |
| R-002 | `env_file` в compose перекроет ожидаемые overrides | Ops | M | M | Smoke запуск compose | Явно держать overrides в `environment:` | Вернуть явный список `environment:` | Maintainer | Open | [`docker-compose.yml`](docker-compose.yml:1) |
| R-003 | Скрипты ломаются при отсутствии `.env.oauth` | DX | M | M | Запуск скрипта без файла | Загрузка `.env.oauth` не должна быть обязательной, но должна давать понятную ошибку при отсутствии ключей | Документировать создание файла | Maintainer | Open | [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py:1) |

## 13) Open Questions

- **OQ-001**: Нужен ли отдельный `README` по конфигам env или достаточно обновить [`docs/setup.md`](docs/setup.md:1) и [`docs/auth.md`](docs/auth.md:1)?
- **OQ-002**: Должны ли runtime переменные quota (например строгий parity) попадать в `.env` и в контейнер, или оставаться дефолтами в [`config.py`](config.py:1)?

### OQ Resolutions

- **OQ-001 Resolution**: нужен отдельный документ по env-файлам и контурам загрузки. Канонический документ: [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1).
- **OQ-002 Resolution**: все переменные, влияющие на runtime контейнера, должны:
  - быть перечислены и документированы;
  - попадать в контейнер явно через [`docker-compose.yml`](docker-compose.yml:1);
  - не иметь скрытых дефолтов в коде (принцип полной прозрачности).
  
  Если переменная не используется в коде — удалить её из [`.env.example`](.env.example:1) и из [`docker-compose.yml`](docker-compose.yml:1).

## 14) ADR links

- [`ADR 0015`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1)

## Appendix A: Runtime env policy (normative)

### A.1 Runtime env injection

Контейнер должен получать runtime env явно через [`docker-compose.yml`](docker-compose.yml:1):

- `env_file` используется только как storage значений.
- `environment:` перечисляет **все** runtime-ключи, которые реально используются кодом прокси.

### A.2 No hidden defaults

Любые дефолты в коде, влияющие на runtime поведение, считаются нарушением прозрачности.

Нормативная реализация должна:

- либо требовать наличие runtime env ключей при старте;
- либо (если ключ truly optional) иметь явную документацию optional-поведения в [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1).


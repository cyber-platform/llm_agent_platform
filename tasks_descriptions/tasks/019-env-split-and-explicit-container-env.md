# Task: Env split `.env` + `.env.oauth` и явная инъекция runtime env в контейнер

## Контекст

- Источник: ошибка при локальном запуске OAuth скрипта — переменные из [`.env`](.env:1) не попадали в процесс VS Code/uv, что приводило к падению в [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py:99).
- Связанные артефакты:
  - [`ADR 0015`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1)
  - [`Spec 019`](plans/019-env-separation-runtime-vs-oauth-bootstrap-spec.md:1)
  - Документ env-политики: [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)
  - Test suite: [`docs/testing/suites/config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md:1)

## Architecture Context References

- [x] [`ADR 0015`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1)
- [ ] [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
- [ ] [`.kilocode/rules/memory-bank/systemPatterns.md`](.kilocode/rules/memory-bank/systemPatterns.md:1)

## Specification References

- [x] [`Spec 019`](plans/019-env-separation-runtime-vs-oauth-bootstrap-spec.md:1)
- [ ] `none` (контрактов schema/OpenAPI не добавляем)

## Test Design References

- [x] [`docs/testing/suites/config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md:1)
- [x] [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Workflow References

- [ ] `none`

## Цель

1) Разделить конфигурацию на runtime и OAuth bootstrap:

- runtime: [`.env`](.env:1) + [`.env.example`](.env.example:1)
- bootstrap: [`.env.oauth`](.env.oauth:1) + [`.env.oauth.example`](.env.oauth.example:1)

2) Сделать загрузку env детерминированной:

- локальные OAuth скрипты загружают [`.env`](.env:1) затем [`.env.oauth`](.env.oauth:1) (override)
- контейнер получает runtime env **явно** из [`docker-compose.yml`](docker-compose.yml:1)

3) Принцип прозрачности: все runtime переменные, используемые кодом, перечислены в `environment:` в [`docker-compose.yml`](docker-compose.yml:1), а не спрятаны в дефолтах.

## Шаги реализации

- [ ] Добавить зависимость для загрузки env-файлов в локальных скриптах (пакет `python-dotenv`) в [`pyproject.toml`](pyproject.toml:1).
- [ ] Добавить [`.env.oauth.example`](.env.oauth.example:1) с bootstrap ключами для OAuth.
- [ ] Обновить [`.env.example`](.env.example:1): оставить только runtime переменные, используемые в контейнере.
- [ ] Обновить [`docs/auth.md`](docs/auth.md:1) и [`docs/setup.md`](docs/setup.md:1) с ссылкой на [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1).
- [ ] Обновить локальные OAuth скрипты:
  - [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py:1)
  - [`scripts/get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py:1)
  
  Требование: загрузка [`.env`](.env:1) + [`.env.oauth`](.env.oauth:1) до импорта [`config.py`](config.py:1) и до импорта [`auth/qwen_oauth.py`](auth/qwen_oauth.py:1).

- [ ] Обновить [`docker-compose.yml`](docker-compose.yml:1) согласно политике явного runtime env:
  - добавить `env_file: .env` как storage значений
  - перечислить все runtime ключи в `environment:`
  - удалить из `environment:` всё, что не используется runtime кодом

- [ ] Провести ревизию runtime env key usage:
  - все ключи, читаемые кодом (через [`config.py`](config.py:1) и прямые `os.environ.get`), должны быть документированы
  - если ключ не используется — удалить из [`.env.example`](.env.example:1) и кода

## Definition of Done

- [ ] Разделение env файлов реализовано по [`ADR 0015`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1)
- [ ] Локальные OAuth скрипты запускаются из VS Code/uv без ручного `export` и не падают на проверках env
- [ ] Runtime env прокси перечислен явно в [`docker-compose.yml`](docker-compose.yml:1)
- [ ] Неиспользуемые env ключи удалены из [`.env.example`](.env.example:1) и из кода
- [ ] Обновлены docs и test-map suite

## Execution Status

- Current State: Архитектура и тест-дизайн зафиксированы (см. [`ADR 0015`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1), [`Spec 019`](plans/019-env-separation-runtime-vs-oauth-bootstrap-spec.md:1), [`docs/testing/suites/config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md:1)).
- Next Step: Начать реализацию с добавления `python-dotenv` и создания [`.env.oauth.example`](.env.oauth.example:1).
- Blockers: none
- Contract Changes: none
- Verification: см. тест-кейсы TC-001..TC-004 в [`docs/testing/suites/config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md:1)


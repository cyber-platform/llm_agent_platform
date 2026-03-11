# Task: Repo layout refactor — перенос нашего кода в `src/model_proxy/` и скриптов в `src/scripts/`

## Контекст

- Источник: необходимость сделать структуру проекта однозначной (наш код отдельно от внешних nested repos), улучшить навигацию и убрать `sys.path` workaround-ы в скриптах.
- Связанные артефакты:
  - [`ADR 0016`](docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md:1)
  - [`Spec 020`](plans/020-repo-layout-src-model_proxy-and-scripts-spec.md:1)
  - Карта компонентов: [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
  - Test suite: [`docs/testing/suites/config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md:1)

## Architecture Context References

- [x] [`ADR 0016`](docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md:1)
- [x] [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)
- [ ] [`.kilocode/rules/memory-bank/systemPatterns.md`](.kilocode/rules/memory-bank/systemPatterns.md:1)

## Specification References

- [x] [`Spec 020`](plans/020-repo-layout-src-model_proxy-and-scripts-spec.md:1)
- [ ] `none` (контрактов schema/OpenAPI не добавляем)

## Test Design References

- [x] [`docs/testing/suites/config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md:1)
- [x] [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Workflow References

- [ ] `none`

## Цель

1) Весь наш runtime код прокси находится в `src/model_proxy/` и импортируется как пакет `model_proxy.*`.
2) Локальные скрипты находятся в `src/scripts/` и импортируют `model_proxy.*` без `sys.path` hacks.
3) Контейнерный запуск производится через `python -m model_proxy`.
4) Документация по компонентам указывает пути до кода (см. [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)).

## Шаги реализации

- [ ] Создать структуру `src/model_proxy/` и перенести туда код из:
  - [`api/`](api)
  - [`auth/`](auth)
  - [`core/`](core)
  - [`services/`](services)
  - [`config.py`](config.py:1)
  - [`main.py`](main.py:1)

- [ ] Добавить `src/model_proxy/__main__.py` как канонический entrypoint.

- [ ] Перенести OAuth скрипты в `src/scripts/`:
  - [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py:1)
  - [`scripts/get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py:1)

- [ ] Обновить импорты по проекту на `model_proxy.*`.

- [ ] Обновить сборку/запуск:
  - [`Dockerfile`](Dockerfile:1) — чтобы запускать `python -m model_proxy`
  - [`docker-compose.yml`](docker-compose.yml:1) — при необходимости

- [ ] Обновить тесты и команды верификации (compileall/unittest) под новый layout.

- [ ] Обновить документацию:
  - [`docs/setup.md`](docs/setup.md:1)
  - [`docs/auth.md`](docs/auth.md:1)
  - [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1) (при необходимости уточнить пути)

## Definition of Done

- [ ] Код прокси импортируется как пакет `model_proxy.*`
- [ ] `python -m model_proxy` запускает прокси
- [ ] Локальные OAuth скрипты работают из `src/scripts/`
- [ ] Unit tests проходят (см. runbook в [`docs/testing/test-map.md`](docs/testing/test-map.md:1))
- [ ] Документация отражает новый layout

## Execution Status

- Current State: Спецификация и ADR готовы (см. [`ADR 0016`](docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md:1), [`Spec 020`](plans/020-repo-layout-src-model_proxy-and-scripts-spec.md:1)).
- Next Step: Создать `src/model_proxy/` и перенести [`config.py`](config.py:1) + [`main.py`](main.py:1) как первые якорные файлы.
- Blockers: none
- Contract Changes: none
- Verification: TC-101, TC-102 из [`docs/testing/suites/config-env-and-layout.md`](docs/testing/suites/config-env-and-layout.md:1)


# Task: Hardening auth/config для стабильной parity-работы

## Контекст
- Источник: [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- Связанные артефакты: [`001-infra-config.md`](tasks_descriptions/backlog/001-infra-config.md), [`002-core-auth.md`](tasks_descriptions/backlog/002-core-auth.md)

## Architecture Context References
- [ ] [`systemPatterns.md`](.kilocode/rules/memory-bank/systemPatterns.md)
- [ ] [`active.md`](.kilocode/rules/memory-bank/active.md)

## Specification References
- [ ] [`005-proxy-adaptation-openai-google-gemini.md`](tasks_descriptions/plans/005-proxy-adaptation-openai-google-gemini.md)
- [ ] `none`

## Test Design References
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md)
- [ ] [`docs/testing/suites/`](docs/testing/suites/)

## Workflow References
- [ ] `none`

## Цель
- Убрать хардкод и стабилизировать auth/discovery/config, чтобы parity режим работал предсказуемо и безопасно.

## Шаги реализации
- [ ] Перенести OAuth client id/secret и чувствительные параметры из [`config.py`](config.py) в env.
- [ ] Обновить [`initialize_auth()`](auth/credentials.py:30) и [`refresh_user_creds()`](auth/credentials.py:63) с явной обработкой ошибок и логированием.
- [ ] Уточнить стратегию project discovery в [`discover_project_id()`](auth/discovery.py:6) и задокументировать требования к env.
- [ ] Добавить тесты/проверки на отсутствие хардкода и корректную инициализацию auth.
- [ ] Обновить `.env.example` и документацию по запуску.

## Definition of Done
- [ ] Изменения реализованы по спецификации
- [ ] Проверки пройдены
- [ ] Документация и связанные артефакты обновлены при необходимости

## Execution Status
- Current State: задача создана, реализация не начата.
- Next Step: подготовить список env-переменных и обновить [`config.py`](config.py).
- Blockers: none.
- Contract Changes: none.
- Verification: not started.


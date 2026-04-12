# Task: Recovery archive smoke для `repo-archiver` в основном проекте

## Контекст
- Источник: обсуждение recovery-проверки после починки архивирования скрытых файлов и AES ZIP для [`tools/repo-archiver`](tools/repo-archiver/README.md:1)
- Связанные артефакты: [`tools/repo-archiver/docs/testing/test-map.md`](tools/repo-archiver/docs/testing/test-map.md:1), [`tools/repo-archiver/docs/testing/suites/encryption-aes.md`](tools/repo-archiver/docs/testing/suites/encryption-aes.md:1), [`docs/testing/test-map.md`](docs/testing/test-map.md:1), [`docs/run/dev.md`](docs/run/dev.md:1), [`docker-compose.yml`](docker-compose.yml:1)

## Architecture Context References
- [ ] [`tools/repo-archiver/README.md`](tools/repo-archiver/README.md:16)
- [ ] [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1)

## Specification References
- [ ] [`tools/repo-archiver/docs/testing/suites/encryption-aes.md`](tools/repo-archiver/docs/testing/suites/encryption-aes.md:1)
- [ ] [`docker-compose.yml`](docker-compose.yml:1)

## Test Design References
- [ ] [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- [ ] Будущий suite recovery-smoke для основного проекта с coverage L3/L4

## Workflow References
- [ ] `none`
- [ ] Для этой задачи позже можно добавить отдельный workflow, если сценарий recovery станет регулярным regression pipeline

## Цель
- Спроектировать и реализовать recovery smoke-сценарий, который доказывает, что архив, созданный через `repo-archiver`, можно использовать для восстановления и запуска основного LLM-сервиса.

## Шаги реализации
- [ ] Зафиксировать детальную coverage matrix для recovery smoke: archive content, restore boot, provider smoke.
- [ ] Создать sandbox flow: сборка архива, распаковка во временную директорию, проверка наличия [`.env`](.env:1) и `secrets/`.
- [ ] Спроектировать запуск восстановленной копии через [`docker-compose.yml`](docker-compose.yml:1) с ожиданием readiness.
- [ ] Спроектировать smoke-запросы к провайдерам `qwen-code` на модели `coder-model` и `openai-chatgpt` на модели `gpt-5.4-mini`.
- [ ] Определить место теста в основном проекте и обновить [`docs/testing/test-map.md`](docs/testing/test-map.md:1).

## Definition of Done
- [ ] Дизайн recovery smoke зафиксирован как отдельный suite или task-spec
- [ ] Понятны входные артефакты, sandbox flow и verification commands
- [ ] Решено, какие проверки относятся к L3, а какие к L4
- [ ] Документация тестового контура обновлена при необходимости

## Execution Status
- Current State: Идея recovery smoke зафиксирована как отдельная задача для последующей детальной проработки; реализация пока не начиналась.
- Next Step: Подготовить coverage matrix и структуру suite для recovery smoke в основном проекте.
- Blockers: none
- Contract Changes: none
- Verification: Наличие задачи [`operational_scope/tasks/038-recovery-archive-smoke-for-repo-archiver.md`](operational_scope/tasks/038-recovery-archive-smoke-for-repo-archiver.md:1)

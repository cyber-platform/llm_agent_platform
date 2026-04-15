# Release Context

## Назначение

Этот файл фиксирует project-specific release binding для `llm_agent_platform`.

Он нужен, чтобы reusable release workflow и release step skills не хардкодили локальные договоренности проекта внутри себя.

Файл не повторяет общий loading order из `AGENTS.md`, а описывает только release-specific context проекта.

## Release Source of Truth

- Engineering SoT для release-ready реализации живет в `docs/`.
- Release запускать только после того, как relevant knowledge уже поднято из `operational_scope/` в `docs/`.
- Completed tasks/plans можно удалять только после такой канонизации.

## Workflow-specific exchange layer

- Для конкретного прогона release workflow допускается временный workflow-specific exchange layer в `operational_scope/realise_project/`.
- Этот слой хранит instance-specific handoff artifacts между шагами release workflow.
- Он не является ни Engineering Documentation SoT, ни Release Documentation Layer.
- После завершения release workflow такие handoff artifacts могут быть удалены.

## Release units

### Root release unit

- `./` — основной репозиторий `llm_agent_platform`.

### Nested release units

- `./services/backend/` when touched
- `./services/frontend/` when touched
- `./services/user_service/` when touched

### Not a release unit

- `./services/web_ui_service/` — temporary donor/reference code, не release unit и планируется к удалению.

Release workflow должен определять changed release units через `project/gitContext.md` и текущий фактический scope изменений.

## Release documentation locations

- root project release notes: `docs/releases/`
- backend release notes: `services/backend/docs/releases/` when touched
- frontend release notes: `services/frontend/docs/releases/` when touched
- user service release notes: `services/user_service/docs/releases/` when touched

Release notes пишутся только для root проекта и тех nested release units, которые реально были изменены в текущем релизе.

## Compose boundaries

- `docker-compose-dev.yml` — актуальный checked development contour, который уже синхронизирован с последней логикой разработки и проверен во время реализации.
- `docker-compose.yml` — release/prod contour предыдущего релиза, который может отстать от фактической актуальной логики `docker-compose-dev.yml`.
- Stable Docker registry/repository naming задается отдельно в `project/dockerReleaseContext.md`.

Release step обязан:

- сравнить `docker-compose.yml` с актуальным `docker-compose-dev.yml`;
- обновить в `docker-compose.yml` не только image tags, но и release-relevant runtime logic, которая уже materialized в dev compose;
- обновлять `docker-compose-dev.yml` только если release work сам по себе меняет development contour по смыслу.

## Publish flow

Release publish flow для этого проекта:

1. шаг `02-docker-cutover` определяет новые release versions для touched release units и обновляет `project/releaseVersionRegistry.json`;
2. локально собираются новые prod-ready Docker images с version tags из `project/releaseVersionRegistry.json`;
3. обновляется `docker-compose.yml` и при необходимости `docker-compose-dev.yml` по смыслу;
4. пользователь вручную запускает локальную проверку через `docker-compose.yml`;
5. только после успешной ручной проверки публикуются новые Docker images в registry;
6. шаг `05-github-release` использует уже зафиксированные версии из `project/releaseVersionRegistry.json` для git tags и GitHub releases.

## Cleanup policy

- Удаляются только completed task artifacts и completed plan artifacts.
- Cleanup допустим только если соответствующее знание уже canonized в `docs/`.
- `operational_scope/tasks_map.md` должен быть синхронизирован с удалением artifacts.
- Если artifact все еще нужен как execution/history evidence, его не нужно удалять автоматически без явного project решения.

## Tagging scope

- Tags готовятся для root repo и всех touched nested release units.
- Если nested release unit не изменялся, отдельный release note и отдельный tag prep для него не делаются.
- Release workflow не должен предполагать фиксированный набор changed repos; он должен определять их по фактическому scope текущего релиза.

## Related files

- `AGENTS.md`
- `project/index.md`
- `project/gitContext.md`
- `project/techContext.md`
- `project/dockerReleaseContext.md`
- `project/releaseVersionRegistry.json`
- `docs/index.md`
- `operational_scope/tasks_map.md`

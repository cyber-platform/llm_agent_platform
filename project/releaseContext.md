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

## Release branch policy

### Intended release branches

- `./` -> `main`
- `./services/backend/` -> `main`
- `./services/frontend/` -> `main`
- `./services/user_service/` -> `main`

### Feature branch naming

- Feature branches должны использовать паттерн `feature-<feature-name>`.
- Pre-release preparation по умолчанию должна выполняться именно в feature branch, а не в intended release branch.
- Branch names вне intended release branches и вне `feature-<feature-name>` не являются допустимым release/preparation source, если для них нет отдельной project-local hotfix policy.

### Preparation branch rule

- Steps подготовки релиза до publication gate должны выполняться в feature branch `feature-<feature-name>`.
- Если preparation идет прямо в intended release branch, workflow не должен silently считать это нормой и обязан запросить explicit user confirmation.
- Presence of feature branch допустима и ожидаема на стадиях readiness, docker cutover, cleanup и release notes.

### Release source rule

- Git tags, GitHub releases и Docker publish flow должны выполняться только из merged HEAD intended release branch для каждого touched release unit.
- Open PR, approved PR или просто наличие feature branch недостаточны для release publication.
- Если preparation выполнена в feature branch, workflow должен пройти PR/merge flow в intended release branch перед publication.

### Whole-run atomicity

- Release workflow для этого проекта работает в режиме `whole-run atomic`.
- Если хотя бы один touched release unit не проходит branch policy текущей стадии или не готов к publication из intended release branch, весь release run блокируется до выравнивания всех touched release units.
- Partial release subset допустим только при явном пересмотре approved release scope и отдельной фиксации этого решения в `release-run.md` как новый release run boundary.

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

1. шаг `01-readiness-gate` фиксирует touched release units, branch matrix и проверяет, что pre-release preparation идет в допустимых preparation branches;
2. шаг `02-docker-cutover` определяет новые release versions для touched release units, обновляет `project/releaseVersionRegistry.json` и готовит preparation-stage Docker contour во время feature-branch preparation;
3. шаг `03-artifact-cleanup` очищает completed operational artifacts, уже поднятые в SoT;
4. шаг `04-release-notes` готовит release notes для root проекта и touched nested release units;
5. после завершения preparation workflow проходит hard publication gate: touched release units должны быть merged в intended release branches;
6. только после merge в intended release branches финальный Docker contour повторно materialize-ится и локально проверяется как publication-stage build с version tags из `project/releaseVersionRegistry.json`;
7. обновляется `docker-compose.yml` и при необходимости `docker-compose-dev.yml` по смыслу;
8. пользователь вручную запускает локальную проверку release contour через `docker-compose.yml`;
9. только после успешной ручной проверки публикуются новые Docker images в registry;
10. шаг `05-github-release` повторно валидирует branch state и использует уже зафиксированные версии из `project/releaseVersionRegistry.json` для git tags и GitHub releases.

## PR/merge evidence

- Если release run требует branch integration, в workflow artifacts должны быть зафиксированы: `repo -> current branch`, `repo -> intended release branch`, `repo -> PR URL`, `repo -> merge commit SHA`, `repo -> final release commit SHA`.
- Step `05-github-release` не должен создавать tag/release без повторной проверки, что target commit является merged HEAD intended release branch.

## Mistaken release recovery

- Если release artifact был создан не из intended release branch, он считается mistaken release.
- Mistaken release remediation должна явно фиксировать: удаление erroneous GitHub release, удаление erroneous git tag, corrective PR/merge flow и final recreated release evidence.
- Reuse того же version tag допустим только если erroneous release artifacts удалены и corrective release выполняется по merged HEAD intended release branch.
- Если ошибочный release успел опубликовать Docker images или другие external artifacts, corrective flow обязан отдельно зафиксировать их remediation status до повторного использования той же версии.

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

# Docker Release Context

## Назначение

Этот файл фиксирует project-local Docker release naming и registry binding для `llm_agent_platform`.

Он нужен, чтобы release workflow step `02-docker-cutover` не выводил naming/tagging conventions только из текущих compose файлов и не гадал, какие образы являются release targets.

## Target registry

- Primary registry: Docker Hub
- Default namespace: `medphisiker`

## Release image names

Для root project release используются следующие release image repositories:

- backend: `medphisiker/llm-agent-platform-backend`
- frontend: `medphisiker/llm-agent-platform-frontend`
- user service: `medphisiker/llm-agent-platform-user-service`

## Release image scope

- `backend` image публикуется только если `./services/backend/` входит в touched release units.
- `frontend` image публикуется только если `./services/frontend/` входит в touched release units.
- `user_service` image публикуется только если `./services/user_service/` входит в touched release units.

## Compose alignment notes

- `docker-compose-dev.yml` может использовать env-driven image names и dev tags, но release target naming для `docker-compose.yml` должен оставаться согласованным с repositories из этого файла.
- Step `02-docker-cutover` должен использовать этот файл вместе с `project/releaseContext.md`, а не полагаться только на текущие image refs в compose.

## Tagging note

- Текущие release tags/versions для root проекта и touched release units хранятся в `project/releaseVersionRegistry.json`.
- Этот файл задает stable repository naming, а не сам registry текущих версий.

## Compose invariant

- `docker-compose.yml` должен всегда ссылаться на актуальные опубликованные release Docker images.
- Для touched release units release step обновляет `docker-compose.yml` на новый release tag после подготовки и проверки новых образов.

## Related files

- `project/releaseContext.md`
- `docker-compose.yml`
- `docker-compose-dev.yml`

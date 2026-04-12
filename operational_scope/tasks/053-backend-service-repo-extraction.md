# Выделение `Backend service` в отдельный repository

## Контекст

Текущий root repo `llm_agent_platform` больше не должен оставаться owner-репозиторием production code backend runtime.

Новый целевой system shape уже зафиксирован в engineering SoT:

- [`docs/services/index.md`](../../docs/services/index.md)
- [`docs/architecture/system-overview.md`](../../docs/architecture/system-overview.md)
- [`docs/architecture/container-view.md`](../../docs/architecture/container-view.md)

Согласно этому framing:

- `llm_agent_platform` является assembled multi-service system;
- `Frontend service` уже живет как отдельный nested repo в [`services/frontend/`](../../services/frontend);
- `Backend service` должен быть выделен в отдельный repository;
- root repo должен сохранить system-level `docs/` как документацию всей системы;
- root repo должен сохранить local stack materialization, прежде всего `docker-compose`, который поднимает `frontend` и `backend` вместе;
- технологический стек оркестрируется через [`HSM`](../../docs/terms/project/terms/hsm.md), но `HSM` не является runtime boundary системы.

Эта задача предназначена для агента-разработчика и должна подготовить безопасное, архитектурно согласованное выделение backend runtime в отдельный repo без потери system-level SoT и local integration ergonomics.

Текущее время постановки задачи: `2026-04-13T02:56:38+10:00`.

## Goal

Выделить текущий backend runtime code и его service-local assets в отдельный `Backend service` repository, оставив в root repo только system assembly layer, system-level documentation и local multi-service materialization artifacts.

## Scope

В scope:

- определение точной границы `Backend service` как отдельного repository;
- перенос backend runtime code, backend tests и backend-local config/assets в новый repo;
- сохранение root repo как system assembly repo;
- сохранение root-level `docs/` как Source of Truth для всей системы `llm_agent_platform`;
- сохранение или переработка root-level `docker-compose` так, чтобы он поднимал `frontend` + `backend` как assembled stack;
- минимальная backend-local documentation page в новом backend repo;
- обновление ссылок, paths и navigation там, где backend boundary materialize-ится в docs/operational artifacts;
- явная фиксация repo boundaries, ownership и migration notes.

Не входит в scope:

- redesign provider semantics, contracts или public API behavior;
- переписывание frontend как full target `Web UI` beyond текущий PoC slice;
- auth/RBAC redesign;
- изменение `HSM` как внешнего stack orchestration tool;
- публикация GitHub repository, если для этого требуются внешние права/ручные действия вне workspace;
- перенос system-level `docs/` в backend repo.

## Canonical references

- [`docs/index.md`](../../docs/index.md)
- [`docs/services/index.md`](../../docs/services/index.md)
- [`docs/architecture/system-overview.md`](../../docs/architecture/system-overview.md)
- [`docs/architecture/container-view.md`](../../docs/architecture/container-view.md)
- [`docs/architecture/component-view.md`](../../docs/architecture/component-view.md)
- [`docs/architecture/component-map.md`](../../docs/architecture/component-map.md)
- [`docs/architecture/web-ui.md`](../../docs/architecture/web-ui.md)
- [`docs/architecture/openai-chat-completions-pipeline.md`](../../docs/architecture/openai-chat-completions-pipeline.md)
- [`docs/providers/index.md`](../../docs/providers/index.md)
- [`docs/testing/index.md`](../../docs/testing/index.md)
- [`docs/terms/project/terms/hsm.md`](../../docs/terms/project/terms/hsm.md)
- [`project/gitContext.md`](../../project/gitContext.md)
- [`operational_scope/tasks/041-software-architecture-documentation.md`](./041-software-architecture-documentation.md)
- [`operational_scope/tasks/045-react-frontend-openai-chatgpt-poc-ui.md`](./045-react-frontend-openai-chatgpt-poc-ui.md)

## Dependencies

- Опирается на уже зафиксированную service topology в `docs/`.
- Должна учитывать существующий nested repo [`services/frontend/`](../../services/frontend).
- Не должна ломать current local-only operator flow `frontend -> backend admin API`.
- Должна быть согласована с текущими git boundaries root repo и nested repos.

## Problem frame для агента

Агенту нужно решить не только file move, но и boundary question:

1. Что именно принадлежит `Backend service` repo, а что остается в root system repo.
2. Как сохранить работоспособный local assembled stack после split.
3. Как не допустить появления нескольких конкурирующих SoT между root docs и backend-local docs.
4. Как мигрировать tests, configs, Docker assets, env examples и run commands без semantic drift.
5. Как оформить backend repo так, чтобы он был автономным service repo, но не пытался стать owner system architecture.

## Required outputs

Агент должен вернуть и по возможности materialize-ить:

1. Конкретный extraction plan по repository boundary.
2. Список директорий/файлов, которые переезжают в backend repo.
3. Список директорий/файлов, которые остаются в root repo.
4. Обновленные root artifacts для assembled stack.
5. Minimal backend-local documentation page в новом repo.
6. Updated references/docs/tasks, если они требуются для consistency.
7. Verification notes: как проверить, что split не сломал local stack и documentation navigation.

## Boundary expectations

Предварительное архитектурное ожидание такое:

- В backend repo должны уйти:
  - runtime code (`llm_agent_platform/` или его service-local successor);
  - backend tests;
  - backend Dockerfile и backend-local run/config assets;
  - backend-local README или `docs/index.md` в одну страницу.
- В root repo должны остаться:
  - `docs/` как system-level SoT;
  - `operational_scope/` root-project уровня;
  - `docker-compose` и иные local assembled stack artifacts;
  - references на `services/frontend/` и `services/backend/` как service repos.

Если в ходе работы обнаружится более точная boundary, агент должен зафиксировать rationale, а не молча отклониться от этой модели.

## Constraints

- Не ломать existing root repo как system assembly repo.
- Не переносить `docs/` из root repo в backend repo.
- Не смешивать root git context с nested frontend repo changes без необходимости.
- Если создается `services/backend/`, нужно явно учитывать новый git boundary и future autonomous repo status.
- Backend-local docs должны быть короткими и service-scoped, без дублирования system architecture.
- Все новые docs и task artifacts писать на русском языке, кроме устойчивых English terms, identifiers и code/runtime artifacts.

## Suggested execution order

1. Зафиксировать целевую backend repo boundary и inventory перемещаемых файлов.
2. Materialize-ить `services/backend/` как новый service-local root.
3. Перенести backend code/tests/assets с минимальным разрушением import/runtime paths.
4. Сохранить или обновить root `docker-compose` под assembled `frontend + backend` stack.
5. Добавить минимальную backend-local documentation page.
6. Обновить root docs/operational references, где materialized новый repo boundary.
7. Проверить локальный запуск и базовые test/build flows настолько, насколько это возможно внутри workspace.

## Verification expectations

Минимально ожидается:

- проверить, что root assembled stack по-прежнему можно поднять локально;
- проверить, что frontend path к backend admin API не сломан по topology;
- проверить, что backend repo имеет автономный минимальный startup/dev context;
- проверить, что root `docs/` по-прежнему описывает систему целиком, а backend-local docs не дублируют system SoT;
- если test/build verification частично невозможна, явно зафиксировать validation gap.

## Definition of Done

- `Backend service` materialized как отдельный repository boundary в `services/backend/` или ином явно зафиксированном target path.
- Root repo остается system assembly repo и не выдает себя за owner backend implementation repo.
- Root `docs/` остаются system-level Source of Truth для всей `llm_agent_platform`.
- Root local stack artifacts поднимают `frontend` и `backend` как assembled system.
- Backend repo содержит короткую service-local documentation page.
- Repo boundaries, ownership и navigation обновлены без silent duplication и без нового SoT drift.
- Есть проверяемый migration/verification trail.

## Initial status

- Current State: planned.
- Next Step: agent-level repository extraction design and materialization.
- Blockers: возможны unknowns по exact packaging/import boundary и по способу initial git initialization для нового backend repo.
- Contract Changes: possible.
- Verification: not run.

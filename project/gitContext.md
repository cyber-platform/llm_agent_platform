# Git Context проекта

## Карта репозиториев

| Path | Описание | Роль |
| --- | --- | --- |
| `./` | Основной репозиторий `llm_agent_platform` | root repo |
| `./.kilo/` | Текущий Kilo-контур проекта | project config/tooling contour |
| `./services/frontend/` | React frontend для PoC monitoring/key management | autonomous nested repo |
| `./services/backend/` | Backend runtime, tests, provider registry и OAuth bootstrap scripts | target autonomous nested repo |
| `./services/user_service/` | Identity/login boundary для local operator/admin contour | autonomous nested repo |
| `./services/web_ui_service/` | Временный donor/reference код для UI-адаптации; не является release unit и планируется к удалению | reference-only service directory |
| `./sot_layers/hyper-graph/` | HyperGraph как автономный nested project со своим `AGENTS.md`, `project/`, `docs/` и `operational_scope/`; хранит skills, rules и workflows, но не является целью release этого проекта | special reference/tooling repo |
| `./externel_projects/` | Внешние reference repositories; их код не является активной целью изменений | nested repos внутри директории |

## Git Boundaries

- Git-команды для основного проекта запускаются из `./`.
- Kilo project config и project-specific skills/rules находятся в `./.kilo/`.
- Если task scope уходит в `./services/frontend/`, git-команды нужно запускать из `./services/frontend/` и не смешивать их с root repo.
- Если task scope уходит в `./services/backend/`, git-команды нужно запускать из `./services/backend/`; root repo должен менять только assembly/docs layer вокруг backend boundary.
- Если task scope уходит в `./services/user_service/`, git-команды нужно запускать из `./services/user_service/`; root repo должен менять только assembly/docs layer вокруг user-service boundary.
- Если task scope уходит в `./sot_layers/hyper-graph/`, нужно переключиться на его local context и запускать git-команды из `./sot_layers/hyper-graph/`.
- `./services/web_ui_service/` считается temporary donor/reference directory и не должен рассматриваться как release unit, если задача явно не направлена на него.
- `./sot_layers/hyper-graph/` может активно изменяться как хранилище skills, rules и workflows, но не должен автоматически считаться release unit root проекта.
- `externel_projects/` считаются reference code, если задача явно не нацелена на них.
- Не смешивай root-project changes и `services/backend/` или `sot_layers/hyper-graph/` changes в одном git context.

## Release notes for repository boundaries

- Release workflow использует этот файл как baseline-карту repo boundaries и candidate nested release units.
- Default nested release units для root проекта: `./services/backend/`, `./services/frontend/`, `./services/user_service/` when touched.
- `./services/web_ui_service/` не является release unit.
- `./sot_layers/hyper-graph/` не является release unit root проекта, even if в него активно вносились methodology/tooling changes.

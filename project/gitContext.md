# Git Context проекта

## Карта репозиториев

| Path | Описание | Роль |
| --- | --- | --- |
| `./` | Основной репозиторий `llm_agent_platform` | root repo |
| `./.kilo/` | Текущий Kilo-контур проекта | project config/tooling contour |
| `./services/frontend/` | React frontend для PoC monitoring/key management | autonomous nested repo |
| `./sot_layers/hyper-graph/` | HyperGraph как автономный nested project со своим `AGENTS.md`, `project/`, `docs/` и `operational_scope/` | autonomous nested repo |
| `./externel_projects/` | Внешние reference repositories; их код не является активной целью изменений | nested repos внутри директории |

## Git Boundaries

- Git-команды для основного проекта запускаются из `./`.
- Kilo project config и project-specific skills/rules находятся в `./.kilo/`.
- Если task scope уходит в `./services/frontend/`, git-команды нужно запускать из `./services/frontend/` и не смешивать их с root repo.
- Если task scope уходит в `./sot_layers/hyper-graph/`, нужно переключиться на его local context и запускать git-команды из `./sot_layers/hyper-graph/`.
- `externel_projects/` и `kilocode/` считаются reference code, если задача явно не нацелена на них.
- Не смешивай root-project changes и `sot_layers/hyper-graph/` changes в одном git context.

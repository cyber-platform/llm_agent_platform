# Git Context проекта

## Карта репозиториев

| Path | Описание | Роль |
| --- | --- | --- |
| `./` | Основной репозиторий `llm_agent_platform` | root repo |
| `./.kilo/` | Текущий Kilo-контур проекта | project config/tooling contour |
| `./externel_projects/` | Внешние reference repositories; их код не является активной целью изменений | nested repos внутри директории |

## Git Boundaries

- Git-команды для основного проекта запускаются из `./`.
- Kilo project config и project-specific skills/rules находятся в `./.kilo/`.
- `externel_projects/` и `kilocode/` считаются reference code, если задача явно не нацелена на них.

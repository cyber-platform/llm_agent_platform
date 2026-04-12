# HSM

## Назначение

`HSM` — внешний stack management tool, через который в проекте управляются service lifecycle, mode switching и синхронизация состава стека.

## Роль в `llm_agent_platform`

- `HSM` не является runtime container системы.
- `HSM` не входит в machine-facing или human-facing API surface платформы.
- В контексте проекта `HSM` используется как технологический механизм управления services и их dev/prod materialization.

## Важно для архитектуры

- В `C4`-диаграммах `HSM` не нужно показывать как внутренний container `llm_agent_platform`.
- Упоминать `HSM` следует в prose как stack management technology для `Frontend service` и `Backend service`.

## External references

- documentation: [https://vlmhyperbenchteam.github.io/hsm/](https://vlmhyperbenchteam.github.io/hsm/)
- repository: [https://github.com/VLMHyperBenchTeam/hsm](https://github.com/VLMHyperBenchTeam/hsm)

## Related documents

- service map: [`index.md`](../../../services/index.md)
- system context: [`system-overview.md`](../../../architecture/system-overview.md)
- container topology: [`container-view.md`](../../../architecture/container-view.md)

# Temporary PoC Index For `openai-chatgpt`

## Назначение

Этот файл больше не является каноническим контейнером архитектуры PoC.

Он сохранён временно как transitional index до закрытия и удаления PoC task artifacts.

## Status

- maturity: `temporary`
- intended fate: удалить после полного закрытия PoC tasks и переноса ссылок на стабильный SoT

## Stable SoT for this PoC slice

- provider semantics: [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- admin read-model boundary: [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)
- live refresh subsystem: [`docs/architecture/admin-monitoring-refresh-subsystem.md`](docs/architecture/admin-monitoring-refresh-subsystem.md:1)
- frontend/UI boundary: [`docs/architecture/web-ui.md`](docs/architecture/web-ui.md:1)
- public pipeline boundary: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
- contracts: [`docs/contracts/`](docs/contracts:1)

## What this file still records

- текущий PoC остаётся local single-user boundary;
- admin surface не публикуется наружу;
- public machine-facing surface остаётся только `/<provider>/<group>/v1/*` и `/<provider>/v1/*` для `openai-chatgpt`;
- operator frontend для PoC остаётся временным delivery slice, а не финальным full Web UI.

## Removal rule

Как только task/planning artifacts перестанут ссылаться на этот файл, он должен быть удалён.

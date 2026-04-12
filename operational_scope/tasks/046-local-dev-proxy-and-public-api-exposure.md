# Локальный dev proxy и внешняя публикация public API для PoC

## Контекст

Для PoC frontend должен работать только локально, а наружу должен открываться только machine-facing OpenAI-compatible API.

Решение уже зафиксировано на уровне architecture freeze:

- local frontend + backend dev proxy;
- public exposure только для `/openai-chatgpt/*`.

## Goal

Собрать delivery setup для локальной разработки frontend/backend и отдельный внешний exposure path только для public OpenAI-compatible API.

## Scope

В scope:

- local dev proxy setup для frontend -> backend;
- docker / compose changes при необходимости;
- runbook или config для `cloudflared` tunnel;
- при необходимости thin reverse proxy layer, если он нужен для path filtering;
- проверка, что admin API и frontend не уходят в публичный exposure path.

Не входит в scope:

- backend business logic;
- frontend UI implementation;
- future production ingress design.

## Canonical references

- [`docs/architecture/web-ui.md`](../../docs/architecture/web-ui.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`docker-compose.yml`](../../docker-compose.yml)
- [`docs/configuration/env-files.md`](../../docs/configuration/env-files.md)

## Dependencies

- Может стартовать после появления минимального frontend/backend runtime skeleton.
- Полный smoke удобно делать после tasks 043 и 045.

## Implementation notes

1. Для local dev использовать frontend proxy вместо CORS-first setup.
2. Public exposure должен публиковать только machine-facing route namespace.
3. Frontend остается только на local URL и не должен туннелиться наружу.
4. Если path filtering прямо в tunnel неудобен, допустим thin proxy перед backend.

## Definition of Done

- Локально frontend работает через proxy на backend.
- Наружу опубликован только public OpenAI-compatible API.
- `admin` routes не доступны через публичный URL.
- Есть короткий ops runbook для запуска demo path на Ubuntu 24.04.

## Execution Status

- Current State: выполнена.
- Next Step: использовать current checked-in delivery boundary как PoC baseline до отдельного ingress/auth hardening stage.
- Blockers: none.

## Completion Notes

- Local dev proxy materialized в `services/frontend/config/dev-server.json`: frontend proxy-ит `/admin` и `/openai-chatgpt` на backend `http://127.0.0.1:4000`.
- Checked-in container delivery boundary materialized в `docker-compose.yml`: backend и frontend публикуются только на localhost (`127.0.0.1:4000` и `127.0.0.1:4173`).
- PoC operator frontend остается local-only service, а machine-facing public namespace ограничивается `openai-chatgpt` API boundary по accepted delivery model из `docs/adr/0024-poc-operator-frontend-delivery-boundary.md`.
- Финальный smoke contour `TS-OPENAI-CHATGPT-POC-SMOKE` фиксирует проверку local/public boundary: frontend и admin surface остаются локальными, внешний demo path должен публиковать только `/openai-chatgpt/*`.

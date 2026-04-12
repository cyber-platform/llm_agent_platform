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

- [`docs/architecture/poc-openai-chatgpt-demo.md`](../../docs/architecture/poc-openai-chatgpt-demo.md)
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

- Current State: запланирована.
- Next Step: materialize dev proxy config и demo exposure runbook.
- Blockers: none.

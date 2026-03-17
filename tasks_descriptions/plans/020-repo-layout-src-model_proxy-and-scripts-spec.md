# Spec: Repo layout refactor в `src/` (runtime package `model_proxy` + `src/scripts/`)

Связанные решения:

- [`ADR 0016`](docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md:1)
- [`ADR 0015`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1)

## 1) Problem and goals

### Problem

Текущая структура смешивает runtime-код прокси и локальные скрипты, а также соседствует с внешними nested repos (например [`qwen-code/`](qwen-code)). Это ухудшает навигацию и приводит к хрупким импортам (см. `sys.path` workaround в [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py:14)).

### Goals

- **G-1**: Весь код прокси хранится в `src/` и оформлен как пакет `model_proxy`.
- **G-2**: Локальные скрипты лежат в `src/scripts/` и импортируют `model_proxy.*` без `sys.path` hacks.
- **G-3**: Контейнерный entrypoint запускается как модуль `python -m model_proxy`.
- **G-4**: Документация содержит карту компонентов и точные пути в репозитории.

## 2) Non-goals

- Не меняем содержимое внешних nested repos (например [`qwen-code/`](qwen-code)).
- Не меняем API-контракт прокси.

## 3) Use cases / User stories

- **US-101**: Разработчик быстро находит компонент по документации (компонент → назначение → путь до кода).
- **US-102**: Разработчик запускает контейнер прокси стандартной командой и получает тот же runtime.
- **US-103**: Разработчик запускает локальные OAuth скрипты из VS Code/uv и импорты стабильны.

## 4) NFR

- **NFR-101 Maintainability**: Импорты не зависят от текущей директории запуска.
- **NFR-102 DX**: LLM-агент может ориентироваться по «карте компонентов».

## 5) Constraints

- **CONS-101**: Python packaging должен поддерживать `src` layout.
- **CONS-102**: Тесты продолжают запускаться через текущий тестовый контур (см. [`docs/testing/test-map.md`](docs/testing/test-map.md:1)).

## 6) Architecture overview (components and boundaries)

### 6.1 Target code layout

- `src/`
  - `src/model_proxy/` — runtime пакет
    - `src/model_proxy/api/`
    - `src/model_proxy/auth/`
    - `src/model_proxy/core/`
    - `src/model_proxy/services/`
    - `src/model_proxy/config.py`
    - `src/model_proxy/__main__.py`
  - `src/scripts/` — локальные scripts/tools

### 6.2 Boundary: external nested repos

- `qwen-code/`, `gemini-cli/`, `kilocode/` считаются внешними reference repos и не являются частью runtime пакета.

## 7) Domain model

Для этой задачи доменная модель — структура модулей и entrypoints:

- **RuntimePackage**: пакет `model_proxy`.
- **LocalScripts**: набор утилит в `src/scripts/`, использующих runtime package.
- **Entrypoint**: `python -m model_proxy`.

## 8) Key models

- `src/model_proxy/config.py` (миграция [`config.py`](config.py:1))
- `src/model_proxy/__main__.py` (миграция логики запуска из [`main.py`](main.py:1))

## 9) Contracts

Контракты API не меняются.

## 10) Test design

Нужен отдельный test design документ для:

- smoke запуска entrypoint `python -m model_proxy`
- smoke запуска OAuth scripts после переноса
- проверок импортов и запуска unit tests

## 11) Coverage matrix

| Requirement | Test Case | Level |
|---|---|---|
| US-101 | TC-101 | L4 (doc review) |
| US-102 | TC-102 | L2 (compose run) |
| US-103 | TC-103 | L2 (script run) |
| NFR-101 | TC-104 | L1 (imports) + L2 (unittest) |

## 12) Risk register

| Risk ID | Risk statement | Category | Prob | Impact | Detection | Mitigation | Contingency | Owner | Status | Links |
|---|---|---|---|---|---|---|---|---|---|---|
| R-101 | Регрессия импортов после переноса в `src/` | Delivery | M | H | `uv run python -m unittest ...` | Поэтапная миграция + smoke тесты | Откат коммита | Maintainer | Open | [`ADR 0016`](docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md:1) |
| R-102 | Docker entrypoint перестанет работать | Ops | M | H | `docker compose up` | Обновить [`Dockerfile`](Dockerfile:1) и [`docker-compose.yml`](docker-compose.yml:1) | Временный запуск старым entrypoint | Maintainer | Open | [`Dockerfile`](Dockerfile:1) |

## 13) Open Questions

- **OQ-101**: Делать ли переезд в `src/` отдельным PR от env-split или объединить? (предпочтительно разделить)
- **OQ-102**: Нужно ли выделять `src/model_proxy/cli/` для будущих команд? (вне scope)


# ADR 0016: Код-лейаут: весь код прокси в `src/` (пакет `src/model_proxy/`), локальные скрипты в `src/scripts/`

## Status
Proposed

## Context

Сейчас структура workspace смешивает:

- runtime-код прокси (контейнерный процесс): [`main.py`](main.py:1), [`config.py`](config.py:1), каталоги [`api/`](api), [`auth/`](auth), [`core/`](core), [`services/`](services)
- локальные одноразовые скрипты (bootstrap/утилиты): [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py:1), [`scripts/get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py:1)
- внешние вложенные репозитории (upstream reference), которые мы не меняем: [`qwen-code/`](qwen-code), [`gemini-cli/`](gemini-cli)

Это усложняет:

- понимание «что является нашим приложением» и что запускается в контейнере;
- поддержку импортов (скрипты вынуждены подправлять `sys.path`, см. [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py:14));
- навигацию для LLM-агента: сложно быстро понять компоненты и где их искать;
- контроль зависимостей и контуров конфигурации (см. [`ADR 0015`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1)).

Дополнительное требование: runtime-конфигурация контейнера должна быть полностью явной (без неочевидных дефолтов и без неиспользуемых переменных).

## Decision

Принять целевой layout, где **весь наш код** расположен в одном месте: `src/`, а внутри `src/` выделены:

1) `src/model_proxy/` — основной пакет прокси (внутри: `api/`, `auth/`, `core/`, `services/`, `config.py`).
2) `src/scripts/` — локальные bootstrap/maintenance скрипты (OAuth и т.п.).
3) Entry point для контейнера — через запуск модуля `model_proxy`.

Внешние вложенные репозитории (например [`qwen-code/`](qwen-code)) остаются на верхнем уровне workspace как upstream reference и не смешиваются с нашим кодом.

### Target layout (proposed)

- `src/`
  - `src/model_proxy/`
    - `src/model_proxy/api/`
    - `src/model_proxy/auth/`
    - `src/model_proxy/core/`
    - `src/model_proxy/services/`
    - `src/model_proxy/config.py`
    - `src/model_proxy/__main__.py` (контейнерный entrypoint)
  - `src/scripts/`
    - `src/scripts/get_oauth_credentials.py`
    - `src/scripts/get_qwen_oauth_credentials.py`

### Entry points

- Контейнер: `python -m model_proxy`.
- Локальные скрипты: запускать из `src/scripts/` и импортировать пакет `model_proxy.*`.

## Options Considered

### Option A: Оставить текущий плоский layout
- Плюсы: минимум изменений.
- Минусы: остаётся смешение ответственности и `sys.path` hacks.

### Option B: Вынести только скрипты в отдельную папку, runtime оставить в корне
- Плюсы: чуть лучше читаемость.
- Минусы: runtime всё равно не оформлен как пакет; импорты остаются хрупкими.

### Option C (выбрано): `src/` как единственная зона нашего кода + `model_proxy` + `scripts`
- Плюсы: единая точка входа для навигации; проще для LLM-агента; явные границы; короткие импорты `model_proxy.*`.
- Минусы: требуется миграция импортов, docker entrypoint, тестов.

## Consequences

### Положительные
- Явная граница: что является нашим кодом (в `src/`), а что внешними nested repos.
- Скрипты не требуют правки `sys.path`.
- Проще документировать компоненты и их локации.

### Негативные / Риски
- Крупное перемещение файлов, риск регрессий в import paths.
- Потребуется обновить [`Dockerfile`](Dockerfile:1) и [`docker-compose.yml`](docker-compose.yml:1).
- Потребуется обновить документацию запуска (например, [`docs/setup.md`](docs/setup.md:1), [`docs/auth.md`](docs/auth.md:1)).

## Implementation Notes (non-normative)

- Миграцию выполнять вместе с ревизией переменных окружения:
  - всё нужное контейнеру должно быть явным и попадать в контейнер (см. [`docker-compose.yml`](docker-compose.yml:1));
  - неиспользуемые переменные удалить из [`.env.example`](.env.example:1) и из [`config.py`](config.py:1).
- Зафиксировать «карту компонентов» в документации с путями до кода (для навигации LLM-агента).

## Review conditions

- Если миграция слишком тяжелая для текущего релиза, рассмотреть поэтапный перенос: сначала `src/` без `packages`, затем выделение `packages`.

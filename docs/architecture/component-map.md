# Component Map (каноническая карта компонентов)

Цель: дать LLM-агенту и разработчику быстрый способ понять:

- какие компоненты есть у сервиса;
- за что они отвечают;
- где лежит код (текущий и целевой путь);
- какие артефакты описывают правила (ADR/spec/docs).

Связанные решения и канонические документы:

- Env split (runtime vs OAuth bootstrap): [`ADR 0015`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1), [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)
- Repo layout `src/` (пока Proposed): [`ADR 0016`](docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md:1)
- Quota rotation + groups: [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)
- OpenAI chat_completions pipeline: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)

## 1) Границы workspace

### 1.1 Наш код (proxy project)

Текущий layout: код находится в корне репозитория (папки [`api/`](api), [`auth/`](auth), [`core/`](core), [`services/`](services), файлы [`main.py`](main.py:1), [`config.py`](config.py:1)).

Целевой layout: весь код прокси переезжает в `src/` и оформляется как пакет `model_proxy` (см. [`ADR 0016`](docs/adr/0016-codebase-layout-separate-runtime-app-and-local-scripts.md:1)).

### 1.2 Внешние nested repos (reference upstream)

Эти директории рассматриваются как внешние, upstream/reference. Их код не меняем, они не входят в runtime пакеты:

- [`qwen-code/`](qwen-code)
- [`gemini-cli/`](gemini-cli)
- [`kilocode/`](kilocode)

## 2) Компоненты прокси

### 2.1 HTTP API слой (OpenAI compatible)

- Назначение: OpenAI compatible endpoints (`/v1/chat/completions`, `/v1/models`), стриминг, tool calling.
- Текущий код:
  - [`api/openai/routes.py`](api/openai/routes.py:1)
  - [`api/openai/transform.py`](api/openai/transform.py:1)
- Целевой код:
  - `src/model_proxy/api/openai/routes.py`
  - `src/model_proxy/api/openai/transform.py`

### 2.2 HTTP API слой (Gemini provider)

- Назначение: provider специфичные маршруты и проксирование в Gemini.
- Текущий код: [`api/gemini/routes.py`](api/gemini/routes.py:1)
- Целевой код: `src/model_proxy/api/gemini/routes.py`

### 2.3 Parity / capture relay

- Назначение: инструменты parity валидации и capture-relay контур.
- Текущий код: [`api/parity/routes.py`](api/parity/routes.py:1)
- Целевой код: `src/model_proxy/api/parity/routes.py`

### 2.4 Auth: credentials, discovery, refresh

- Назначение: обнаружение источников авторизации, refresh токенов, fail-fast диагностика.
- Текущий код:
  - [`auth/credentials.py`](auth/credentials.py:1)
  - [`auth/discovery.py`](auth/discovery.py:1)
  - [`auth/qwen_oauth.py`](auth/qwen_oauth.py:1)
- Целевой код:
  - `src/model_proxy/auth/credentials.py`
  - `src/model_proxy/auth/discovery.py`
  - `src/model_proxy/auth/qwen_oauth.py`

### 2.5 Core: logging, utils, models

- Назначение: shared утилиты и модели.
- Текущий код:
  - [`core/logging.py`](core/logging.py:1)
  - [`core/models.py`](core/models.py:1)
  - [`core/utils.py`](core/utils.py:1)
- Целевой код:
  - `src/model_proxy/core/logging.py`
  - `src/model_proxy/core/models.py`
  - `src/model_proxy/core/utils.py`

### 2.6 Services: transport, http pool, routing

- Назначение: инфраструктурные сервисы (http pool, quota transport, account router).
- Текущий код: `services/` (пример: [`services/http_pool.py`](services/http_pool.py:1))
- Целевой код: `src/model_proxy/services/`

### 2.7 Конфигурация runtime

- Назначение: единая точка конфигурации через env.
- Текущий код: [`config.py`](config.py:1)
- Целевой код: `src/model_proxy/config.py`
- Правила env: [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)

### 2.8 Entrypoint прокси

- Назначение: собрать Flask app, зарегистрировать blueprints, выполнить init auth, запустить server.
- Текущий код: [`main.py`](main.py:1)
- Целевой код: `src/model_proxy/__main__.py`

## 3) Локальные tools (OAuth bootstrap)

- Назначение: одноразовое получение credentials и запись в `secrets/`.
- Текущий код:
  - [`scripts/get_oauth_credentials.py`](scripts/get_oauth_credentials.py:1)
  - [`scripts/get_qwen_oauth_credentials.py`](scripts/get_qwen_oauth_credentials.py:1)
- Целевой код:
  - `src/scripts/get_oauth_credentials.py`
  - `src/scripts/get_qwen_oauth_credentials.py`

Bootstrap env правила: [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)

## 4) Тестовый контур

Канонический индекс: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)


# Component Map (каноническая карта компонентов)

Цель: дать LLM-агенту и разработчику быстрый способ понять:

- какие компоненты есть у сервиса;
- за что они отвечают;
- где лежит актуальный runtime-код;
- какие артефакты описывают правила (ADR/spec/docs).

Связанные решения и канонические документы:

- Env split (runtime vs OAuth bootstrap): [`docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md`](docs/adr/0015-env-separation-runtime-vs-oauth-bootstrap.md:1), [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)
- Provider-centric routing: [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1)
- Quota rotation + groups: [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)
- OpenAI chat completions pipeline: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
- Provider index and status matrix: [`docs/providers/README.md`](docs/providers/README.md:1)

## 1) Границы workspace

### 1.1 Наш код

Актуальный runtime layout:
- пакет [`llm_agent_platform/`](llm_agent_platform:1)
- локальные bootstrap scripts в [`scripts/`](scripts:1)
- contracts и канон в [`docs/`](docs:1)

Для понимания архитектуры текущей системы Source of Truth нужно брать из актуального layout, а не из временных migration narrative.

### 1.2 Внешние nested repos (reference upstream)

Эти директории рассматриваются как внешние, upstream/reference. Их код не меняем, они не входят в runtime пакеты:

- [`qwen-code/`](qwen-code)
- [`gemini-cli/`](gemini-cli)
- [`kilocode/`](kilocode)

## 2) Компоненты прокси

### 2.1 HTTP API слой (OpenAI-compatible)

- Назначение: provider-scoped OpenAI-compatible endpoints, стриминг, tool calling.
- Текущий код:
  - [`llm_agent_platform/api/openai/routes.py`](llm_agent_platform/api/openai/routes.py:1)
  - [`llm_agent_platform/api/openai/transform.py`](llm_agent_platform/api/openai/transform.py:1)
  - [`llm_agent_platform/api/openai/pipeline.py`](llm_agent_platform/api/openai/pipeline.py:1)

### 2.2 HTTP API слой (Gemini native provider surface)

- Назначение: provider специфичные маршруты и проксирование в Gemini.
- Текущий код: [`llm_agent_platform/api/gemini/routes.py`](llm_agent_platform/api/gemini/routes.py:1)

### 2.3 Parity / capture relay

- Назначение: инструменты parity валидации и capture-relay контур.
- Текущий код: [`llm_agent_platform/api/parity/routes.py`](llm_agent_platform/api/parity/routes.py:1)

### 2.4 Auth: credentials, refresh, provider-specific state

- Назначение: обнаружение источников авторизации, refresh токенов, fail-fast диагностика.
- Текущий код:
  - [`llm_agent_platform/auth/credentials.py`](llm_agent_platform/auth/credentials.py:1)
  - [`llm_agent_platform/auth/discovery.py`](llm_agent_platform/auth/discovery.py:1)
  - [`llm_agent_platform/auth/qwen_oauth.py`](llm_agent_platform/auth/qwen_oauth.py:1)

Provider-specific auth semantics должны документироваться на отдельных страницах в [`docs/providers/`](docs/providers:1).

### 2.5 Core: logging, utils, models

- Назначение: shared утилиты и модели.
- Текущий код:
  - [`llm_agent_platform/core/logging.py`](llm_agent_platform/core/logging.py:1)
  - [`llm_agent_platform/core/models.py`](llm_agent_platform/core/models.py:1)
  - [`llm_agent_platform/core/utils.py`](llm_agent_platform/core/utils.py:1)

### 2.6 Services: transport, registry, routing, state

- Назначение: инфраструктурные сервисы платформы.
- Текущий код:
  - [`llm_agent_platform/services/http_pool.py`](llm_agent_platform/services/http_pool.py:1)
  - [`llm_agent_platform/services/provider_registry.py`](llm_agent_platform/services/provider_registry.py:1)
  - [`llm_agent_platform/services/account_router.py`](llm_agent_platform/services/account_router.py:1)
  - [`llm_agent_platform/services/account_state_store.py`](llm_agent_platform/services/account_state_store.py:1)

Граница ответственности в provider-centric каноне:
- provider descriptor contracts задают declarative configuration boundary через [`docs/contracts/config/provider-descriptor.schema.json`](docs/contracts/config/provider-descriptor.schema.json:1) и [`docs/contracts/config/provider-registry.schema.json`](docs/contracts/config/provider-registry.schema.json:1);
- [`llm_agent_platform/services/provider_registry.py`](llm_agent_platform/services/provider_registry.py:1) резолвит descriptor boundary и catalog metadata;
- runtime adapters исполняют transport/auth/runtime contract внутри [`llm_agent_platform/api/openai/providers/`](llm_agent_platform/api/openai/providers/base.py:1);
- strategies исполняют policy boundary внутри [`llm_agent_platform/api/openai/strategies/`](llm_agent_platform/api/openai/strategies/base.py:1).

Usage-limits capability трактуется отдельно от routing/runtime readiness:
- quota exhaustion всегда фиксируется по runtime error path;
- proactive usage polling допустим только как optional observability and monitoring capability provider;
- нормализованный usage snapshot не заменяет основной quota enforcement path.

### 2.7 Конфигурация runtime

- Назначение: единая точка конфигурации через env.
- Текущий код: [`llm_agent_platform/config.py`](llm_agent_platform/config.py:1)
- Правила env: [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)

### 2.8 Entrypoint платформы

- Назначение: собрать Flask app, зарегистрировать blueprints, выполнить init auth, запустить server.
- Текущий код: [`llm_agent_platform/__main__.py`](llm_agent_platform/__main__.py:1)

## 3) Локальные tools

- Назначение: одноразовое получение credentials и запись в `secrets/`.
- Текущий код:
  - [`scripts/get_gemini-cli_credentials.py`](scripts/get_gemini-cli_credentials.py:1)
  - [`scripts/get_qwen-code_credentials.py`](scripts/get_qwen-code_credentials.py:1)

Bootstrap env правила: [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)

Именование bootstrap scripts синхронизировано с provider ids:
- [`scripts/get_gemini-cli_credentials.py`](scripts/get_gemini-cli_credentials.py:1)
- [`scripts/get_qwen-code_credentials.py`](scripts/get_qwen-code_credentials.py:1)

## 4) Тестовый контур

Канонический индекс: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

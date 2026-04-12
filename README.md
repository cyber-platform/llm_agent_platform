# LLM Agent Platform

**LLM Agent Platform** — это provider-centric платформа для LLM-агентов и developer tools, которая предоставляет единый OpenAI-compatible API поверх нескольких провайдеров и сохраняет provider-specific особенности внутри отдельных интеграций.

---

## ✨ Что дает платформа

1. **Единый OpenAI-compatible вход для агентных инструментов**
   - Подключение через provider-scoped маршруты `/<provider_name>/v1/*` и `/<provider_name>/<group_name>/v1/*`.
   - Явный выбор provider через URL, а не через эвристики по имени модели.

2. **Поддержка нескольких provider integrations**
   - Платформа не привязана к одному provider.
   - Одинаковые `model_id` у разных providers являются нормальным сценарием и не конфликтуют благодаря provider namespace.

3. **Provider-local routing и account groups**
   - Группы аккаунтов живут внутри namespace конкретного provider.
   - Модели и account pools изолируются на уровне `(provider_id, group_id)`.

4. **Единый архитектурный канон и contracts**
   - Общая архитектура фиксируется в [`docs/architecture/`](docs/architecture:1).
   - Contracts фиксируются в [`docs/contracts/`](docs/contracts:1).
   - Provider-specific особенности документируются отдельно в [`docs/providers/`](docs/providers:1) и индексируются в [`docs/providers/index.md`](docs/providers/index.md:1).

5. **Платформа для эволюции provider-specific runtime adapters**
   - Общий OpenAI-compatible surface остается стабильным.
   - Специфика авторизации, runtime transport и usage limits инкапсулируется внутри provider adapters.

---

## 🧭 Архитектурная модель

Платформа строится вокруг трех уровней:
- provider-scoped routing;
- provider registry и provider-local catalogs;
- runtime adapters и execution strategies
- account groups

При этом discovery-based catalogs остаются ожидаемой capability платформы, но текущие active providers могут использовать только static bootstrap catalog.

Канон зафиксирован в [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1) и [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1).

---

## 🛠️ Быстрый старт

### 1. Авторизация

Для quota-based providers используйте соответствующие OAuth bootstrap scripts:
```bash
uv run python scripts/get_gemini-cli_credentials.py
```
Подробности:
- [`docs/auth.md`](docs/auth.md:1)
- provider-specific страницы в [`docs/providers/`](docs/providers:1)

### 2. Запуск через Docker
```bash
cp .env.example .env
docker-compose up -d --build
```

### 3. Подключение к IDE

#### Вариант А: OpenAI Compatible
| Параметр | Значение |
| :--- | :--- |
| **Base URL** | `http://localhost:4000/<provider_name>/v1` |
| **API Key** | `any-string` |
| **Provider** | OpenAI Compatible |

Пример:
- `http://localhost:4000/gemini-cli/v1`
- `http://localhost:4000/qwen-code/v1`
- `http://localhost:4000/openai-chatgpt/v1`

#### Вариант Б: Native Gemini
| Параметр | Значение |
| :--- | :--- |
| **Base URL** | `http://localhost:4000` |
| **API Key** | `any-string` |
| **Provider** | Gemini (Google AI Studio / Vertex AI) |

## 📖 Документация

- [Видение проекта](./docs/vision.md)
- [Настройка авторизации](./docs/auth.md)
- [Установка и развертывание](./docs/setup.md)
- [Сценарии запуска](./docs/run/index.md)
- [Использование платформы](./docs/usage.md)
- [Карта компонентов](./docs/architecture/component-map.md)
- [Каталог провайдеров](./docs/providers/index.md)
- [Provider: `openai-chatgpt`](./docs/providers/openai-chatgpt.md)

---

## ❤️ Принцип документации

Source of Truth для актуальной архитектуры находится в [`docs/`](docs:1). Временные планы и task-артефакты не должны быть обязательными для понимания текущего состояния системы.

---
*Проект распространяется под лицензией MIT.*

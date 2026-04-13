# План реализации PoC2 по приоритету простоты и скорости

## Статус зрелости

- Статус: `candidate for freeze`
- Назначение: implementation ordering для быстрого доведения `PoC2` до демонстрационного состояния
- Основа framing: provider-centric архитектура с provider-local routing внутри группы аккаунтов/пользователей

## Цель

Быстро довести `PoC2` до состояния, в котором платформа:

- имеет цельный operator/admin flow;
- показывает базовую авторизацию и monitoring surface;
- собирает ключевые runtime-метрики;
- демонстрирует provider-local балансировку и наблюдаемость;
- не уходит в дорогие архитектурные ветки вроде cross-provider routing и generic dynamic provider registration.

## Scope

### В scope

- auth UI и интеграция с `user_service`;
- backend/admin auth;
- `health-check` endpoints;
- `Prometheus` и `Grafana`;
- provider/group/account metrics;
- `TTFT`, `TPOT`, `input/output/total tokens`, `cost`;
- нагрузочные сценарии;
- при наличии времени — lightweight `A2A Agent Registry`;
- во вторую очередь — provider page для `qwen`.

### Вне scope

- cross-provider routing;
- generic dynamic provider registration для произвольных adapter types;
- `MLflow`;
- guardrails;
- полноценный production-grade `RBAC` + audit subsystem.

## Ключевые constraints

- Routing в `PoC2` трактуется как provider-local, а не global cross-provider.
- Текущая стратегия балансировки внутри группы — `round robin`.
- Статистика и monitoring ведутся per provider, per group и per account.
- `web_ui_service` используется только как donor-код для UI/auth patterns и не входит в итоговую runtime-сборку.
- Целевой набор сервисов: `services/backend`, `services/frontend`, `services/user_service`.

## Freeze decisions для materialization Priority 1

Эти решения зафиксированы как достаточный baseline для перехода от плана к taskset decomposition.

### 1. JWT verification path

- `services/backend` валидирует JWT от `services/user_service` через shared secret.
- Отдельный introspection endpoint и public-key flow в быстрый контур не входят.
- Это временное решение для `PoC2`, выбранное по критерию минимальной интеграционной стоимости.

### 2. Role mapping

- `developer` трактуется как `admin` для operator/admin surface.
- `user` в быстрый контур не получает mutating admin capabilities.
- Роль `observer` пока не вводится как отдельная обязательная реализация.

### 3. Admin auth scope

- JWT auth применяется только к `/admin/*`.
- Public OpenAI-compatible provider routes не смешиваются с admin auth boundary.
- Platform API keys для публичного provider surface сохраняются как отдельный auth mechanism.

### 4. Frontend token baseline

- Frontend использует простой PoC baseline без refresh-token flow.
- После login UI хранит access token и использует его для admin API запросов.
- Logout очищает локальный auth state и возвращает пользователя на login screen.

## Порядок реализации по простоте и скорости

## Приоритет 1 — самые быстрые и дешевые шаги

### 1. Health-check endpoints для всех сервисов

- Добавить `health-check` endpoints для `services/backend`, `services/frontend` и `services/user_service`.
- Начать с `services/backend` как с наиболее критичной runtime-границы для demo path.
- Для `services/frontend` достаточно дешевого container/nginx health contour.
- Это самый дешевый и изолированный шаг в operational baseline.

Оценка:

- Скорость: высокая
- Сложность: низкая
- Зависимости: нет

### 2. Admin auth через `user_service`

- Защитить `/admin/*` через JWT из `services/user_service`.
- Использовать уже существующие login, roles и brute-force protection.
- Для быстрого контура использовать shared JWT secret.

Оценка:

- Скорость: высокая
- Сложность: низкая/средняя
- Зависимости: адаптация `user_service` под текущую сборку

### 3. Стильная страница авторизации во frontend

- Адаптировать login page из `services/web_ui_service/frontend`.
- Переносить только UI и UX-паттерны, без миграции всего сервиса.
- Сделать это базовой entry page для operator/admin UI.

Оценка:

- Скорость: высокая
- Сложность: низкая
- Зависимости: пункт 2

### 4. Protected frontend shell

- Добавить auth state, logout и protected admin flow.
- Убрать сценарий безавторизованного входа в admin UI.
- Сохранить текущий monitoring shell как основной post-login screen.

Оценка:

- Скорость: высокая
- Сложность: низкая/средняя
- Зависимости: пункты 2 и 3

## Приоритет 2 — быстрые high-value улучшения observability

### 5. `Prometheus` metrics в backend

- Добавить request count, status codes, route/provider/group labels и latency histogram.
- Предпочесть быстрый `Prometheus`-first путь вместо полного `OpenTelemetry`-first контура.
- Это закрывает большую часть минимального monitoring scope быстрее и дешевле.

Оценка:

- Скорость: средняя
- Сложность: средняя
- Зависимости: желательно после пункта 1

### 6. `Grafana` + `Prometheus` в `docker-compose`

- Добавить сервисы мониторинга в локальную сборку.
- Подготовить минимум 2-3 дашборда: latency, traffic split, status codes.
- Использовать это как основной demo-layer для observability.

Оценка:

- Скорость: средняя
- Сложность: средняя
- Зависимости: пункт 5

### 7. CPU метрики

- Добавить экспорт process/system CPU, например через `psutil`.
- Закрыть недостающий пункт минимального мониторинга из задания.
- Включить CPU panel в базовый dashboard.

Оценка:

- Скорость: средняя
- Сложность: средняя
- Зависимости: пункт 5

## Приоритет 3 — provider-local routing observability

### 8. `TTFT` / `TPOT` / token metrics

- Инструментировать stream и non-stream path.
- Считать `TTFT`, `TPOT`, `input_tokens`, `output_tokens`, `total_tokens`.
- Использовать уже существующий usage path как baseline.

Оценка:

- Скорость: средняя
- Сложность: средняя
- Зависимости: пункт 5

### 9. `Cost estimation`

- Добавить provider-local pricing table.
- Считать estimated cost на основе token usage.
- Показывать cost в metrics/read-model/reporting.

Оценка:

- Скорость: средняя
- Сложность: средняя
- Зависимости: пункт 8

### 10. Health-aware routing внутри группы

- Формализовать текущую механику живых аккаунтов как provider-local health-aware selection.
- Использовать cooldown/exhaustion/account state как основу.
- Не выходить в cross-provider semantics.

Оценка:

- Скорость: средняя
- Сложность: средняя
- Зависимости: текущий account state runtime уже существует

### 11. Явная фиксация `round robin` как текущего routing baseline

- Документировать текущую стратегию как provider-local round robin внутри группы.
- Уточнить, что latency/statistics относятся к аккаунтам внутри provider group.
- Не заявлять global latency router между providers.

Оценка:

- Скорость: высокая
- Сложность: низкая/средняя
- Зависимости: нет жестких

## Приоритет 4 — после базового demo-ready контура

### 12. Нагрузочные тесты

- Добавить сценарии concurrency, account/provider failures и peak load.
- Мерить throughput, latency и устойчивость балансировщика.
- Делать это после появления metrics и dashboards.

Оценка:

- Скорость: средняя
- Сложность: средняя
- Зависимости: пункты 5-10

### 13. Provider page для `qwen`

- Добавить во frontend вторую provider page.
- Использовать это как демонстрацию multi-provider surface.
- Не требовать полного parity с `openai-chatgpt` на первом шаге.

Оценка:

- Скорость: средняя
- Сложность: средняя
- Зависимости: базовый auth + frontend shell

## Приоритет 5 — optional / stretch goals

### 14. Lightweight `A2A Agent Registry`

- Сделать минимальный registry для `Agent Card`.
- Допустим file-backed или lightweight backend module.
- Реализовывать только если базовый demo-ready contour уже собран.

Оценка:

- Скорость: средняя
- Сложность: средняя
- Зависимости: нет критичных, но ниже по demo value

### 15. `Langfuse` вместо `MLflow`

- Если нужна LLM/agent tracing story, подключать `Langfuse`, а не `MLflow`.
- Это richer observability layer, но не самый быстрый путь к завершению `PoC2`.

Оценка:

- Скорость: ниже средней
- Сложность: средняя/выше средней
- Зависимости: лучше после базовых metrics

## Рекомендуемая последовательность спринта

1. Адаптация `user_service` под текущую сборку.
2. JWT verify в `services/backend` для `/admin/*`.
3. Login page и protected shell в `services/frontend`.
4. `health-check` для backend.
5. `health-check` contour для всех сервисов.
6. `Prometheus` metrics.
7. `Grafana` dashboards и `docker-compose` assembly.
8. CPU metrics.
9. `TTFT` / `TPOT` / tokens.
10. `Cost estimation`.
11. Health-aware routing inside provider group.
12. Нагрузочные тесты.
13. Provider page для `qwen`.
14. Optional: `A2A Agent Registry`.
15. Optional: `Langfuse`.

## Deliverables

- authenticated admin/operator UI;
- service-wide `health-check` endpoints и backend `/metrics`;
- `Prometheus` + `Grafana` dashboards;
- provider/group/account-level runtime metrics;
- `TTFT`, `TPOT`, token usage и cost estimation;
- нагрузочный test/report contour;
- optional second provider page для `qwen`;
- optional lightweight `A2A Agent Registry`.

## Canonical references

- `operational_scope/plans/poc2/poc2.md`
- `docs/vision.md`
- `docs/architecture/component-map.md`
- `docs/architecture/openai-chat-completions-pipeline.md`
- `docs/architecture/admin-monitoring-read-model.md`
- `docs/providers/index.md`
- `operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md`

## Open questions и white spots

- JWT verification path: shared secret или отдельный verify/introspection endpoint.
- Нужна ли уже сейчас роль `observer`, или для быстрого контура достаточно `admin only`.
- Нужен ли `A2A Agent Registry` как отдельный service или хватит backend module.
- Нужно ли для `qwen` сразу делать parity slice или достаточно отдельной provider page.

## Recommendation for freeze

- Freeze quick scope на пунктах `1-12`.
- Пункты `13-15` считать stretch goals.
- Dynamic provider registration и cross-provider routing явно оставить вне текущего `PoC2` implementation path.

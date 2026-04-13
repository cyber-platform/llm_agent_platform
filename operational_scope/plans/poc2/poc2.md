**Инфраструктурный трек | Разработка Агентной платформы**

## Текущий статус

- Статус: `mini-release baseline materialized`
- Текущий assembled contour включает `services/backend`, `services/frontend`, `services/user_service`
- Priority 1 выполнен: health-check baseline, интеграция `user_service`, backend admin JWT guard, frontend login и protected admin shell materialized
- Этот файл теперь фиксирует не только исходное задание, но и текущий статус реализации

В этом домашнем задании вы разработаете **агентную платформу**. Платформа должна позволять регистрировать A2A‑агентов и подключать различные LLM‑провайдеры, а также умно маршрутизировать запросы и собирать телеметрию. Работа разделена на несколько модулей, чтобы вы могли выбрать уровень сложности.

Для каждого уровня подготовьте документацию: архитектурные диаграммы, описания API, инструкции по запуску и развёртыванию, отчёты о тестировании и сравнении стратегий балансировки.

**Уровень 1 Минимальный прототип: LLM‑провайдеры, балансировщик и базовый мониторинг**

Задачи:

1. Окружение и деплой. Используйте Docker Compose для развёртывания всех компонентов (да).
2. Сконфигурируйте несколько тестовых LLM‑провайдеров (это могут быть реальные API, например OpenAI и Anthropic, либо локальные мок‑сервисы) (да);
3. Простейший LLM‑балансировщик. Реализуйте прокси, который получает запросы на генерацию и распределяет их между провайдерами по названию моделей, а в случае одинаковых реплик, по круговому алгоритму (round robin) или статическому набору весов.(да)
    
4. Минимальный мониторинг.
    - Интегрируйте OpenTelemetry для логирования входящих запросов и времени ответа. Снимайте метрики: число запросов, средняя/хвостовая латентность (p50/p95), коды ответов и загруженность CPU.
    - Экспортируйте эти метрики в Prometheus и настройте пару простых дашбордов в Grafana (например, графики латентности и распределения трафика по провайдерам) (в работе / следующий приоритет).
    - Добавьте health‑check endpoint для каждого сервиса (да, materialized для `backend`, `frontend`, `user_service`).

**Уровень 2 Реестры агентов и умная маршрутизация**

Задачи:

1. A2A Agent Registry. Реализуйте сервис реестра, позволяющий регистрировать A2A‑агентов с их Agent Card (имя, описание, поддерживаемые методы) и получать список или конкретную карточку по запросу.
2. Добавьте динамическую регистрацию LLM‑провайдеров. Сохраняйте для каждого провайдера URL, цену за токен, лимиты, приоритет.
3. Расширенный LLM/Agent‑балансировщик.
    
    Реализуйте более сложные стратегии: latency‑based routing и health‑aware routing. Измеряйте среднее время ответа каждого провайдера и отдавайте приоритет быстрому/здоровому. В случае ошибок (timeouts, 5xx) временно убирайте провайдера из пула. (частично есть: provider-local account health/cooldown/exhaustion contour)
    
4. Наблюдаемость и трассировки.
    - Добавьте метрики TTFT (time‑to‑first‑token), TPOT (time-per-ouput-token), общее число входных/выходных токенов и стоимость запроса.
    - Подключите MLFlow для трасирования работы Агентов и LLM. (если делать, то скорее через Langfuse; пока не materialized)

**Уровень 3 Продвинутая платформа и дополнительные функции**

Задачи:

1. Добавьте концепцию Guardrails, реализуйте фильтр, который проверяет запросы на попытки prompt‑injection, утечку секретов и другие нарушения. (не делаем)
2. Реализуйте механизм авторизации. Используйте токены для авторизации агентов и LLM (частично выполнено: public provider surface использует API-ключи, admin surface использует JWT через `user_service`; full RBAC еще не materialized).
3. Тестирование и эксплуатация. Проведите нагрузочные тесты: создайте сценарии с большим числом одновременных запросов, отказами провайдеров и пиковыми нагрузками. Измерьте throughput, латентность и устойчивость балансировщика.

## Что уже зафиксировано как результат mini-release

### Materialized

- `docker-compose`-based assembled dev contour с тремя сервисами: `backend`, `frontend`, `user_service`
- provider-local routing и текущий `round robin` baseline внутри account groups
- public platform API keys для `openai-chatgpt`
- service-wide health-check endpoints/probes
- `user_service` как identity boundary для operator/admin login
- backend admin JWT guard для `/admin/*`
- frontend login page и protected admin shell
- documented testing contour для health и auth baseline

### Следующий приоритет

- `Prometheus` + `Grafana`
- CPU metrics
- `TTFT` / `TPOT` / tokens / cost
- нагрузочные тесты
- provider page для `qwen`

## Связанные артефакты

- [`operational_scope/plans/poc2/poc2-priority-implementation-plan.md`](./poc2-priority-implementation-plan.md)
- [`docs/auth.md`](../../../docs/auth.md)
- [`docs/services/index.md`](../../../docs/services/index.md)
- [`docs/testing/test-map.md`](../../../docs/testing/test-map.md)

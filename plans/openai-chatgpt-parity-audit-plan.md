# Plan: parity audit for `openai-chatgpt`

## Context

Этот план нужен, чтобы коротко зафиксировать:
- где наша реализация уже совпадает с reference;
- где есть расхождения;
- что именно можно довести до полного соответствия;
- какой объём изменений действительно нужен.

Основные источники:
- task: [`tasks_descriptions/tasks/016-gpt-integration.md`](tasks_descriptions/tasks/016-gpt-integration.md)
- наш runtime provider: [`llm_agent_platform/api/openai/providers/openai_chatgpt.py`](llm_agent_platform/api/openai/providers/openai_chatgpt.py)
- наш OAuth manager: [`llm_agent_platform/auth/openai_chatgpt_oauth.py`](llm_agent_platform/auth/openai_chatgpt_oauth.py)
- наши тесты: [`llm_agent_platform/tests/test_openai_chatgpt_runtime.py`](llm_agent_platform/tests/test_openai_chatgpt_runtime.py)
- reference provider: [`externel_projects/kilocode/src/api/providers/openai-codex.ts`](externel_projects/kilocode/src/api/providers/openai-codex.ts)
- reference OAuth: [`externel_projects/kilocode/src/integrations/openai-codex/oauth.ts`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts)
- reference usage limits: [`externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts`](externel_projects/kilocode/src/integrations/openai-codex/rate-limits.ts)

## Что уже в целом совпадает

1. **OAuth bootstrap и refresh flow**
   - У нас уже есть bootstrap script и PKCE flow.
   - Есть persisted OAuth state.
   - Есть forced refresh при auth failure.

2. **Private backend transport**
   - У нас runtime уже идёт в private backend, а не в public OpenAI endpoint.
   - Уже используются provider-specific headers и provider-scoped routes.

3. **Static catalog и provider-local groups**
   - Static catalog уже включён в descriptor.
   - Provider работает через общий platform pipeline и account router.

4. **Monitoring-only usage contour**
   - Usage monitoring уже отделён от routing decisions.

## Расхождения с reference

### 1. Tool-call parity

**Где расходимся**
- В нашей реализации tool schema для `openai-chatgpt` сейчас упрощена и более жёсткая.
- Мы не повторяем special-case для MCP tools, который есть в reference.
- Мы не нормализуем tool names формата `mcp__...` в духе reference.
- Мы не санитизируем `call_id` так же строго, как reference.

**Что хотим сделать**
- Добавить parity-логику для MCP tool names.
- Сделать отдельную ветку для MCP tool schemas.
- Добавить санитизацию и ограничение длины `call_id`.

**Для чего это нужно**
- Снизить риск несовместимости с native tool calling.
- Убрать расхождения на сложных tool schemas.
- Повысить совместимость с tool-call поведением из reference.

**Что это даёт**
- Более стабильную работу tools.
- Меньше неожиданных ошибок валидации на upstream стороне.
- Лучший parity с `openai-codex` reference.

### 2. Streaming tool-event parity

**Где расходимся**
- Reference хранит последний `tool call id/name` и использует его для delta-событий, если upstream не прислал эти поля прямо в текущем событии.
- У нас эта логика выражена слабее.

**Что хотим сделать**
- Добавить tracking последнего tool call identity.
- Использовать его при обработке `response.function_call_arguments.delta` и близких событий.

**Для чего это нужно**
- Чтобы tool-call-only streams и неполные delta события не терялись.
- Чтобы потоковое поведение было ближе к reference.

**Что это даёт**
- Более надёжный streaming контур.
- Меньше потерь аргументов tool call в edge-cases.
- Лучшую воспроизводимость поведения reference.

### 3. OAuth error classification

**Где расходимся**
- Reference различает обычную refresh ошибку и сценарий `invalid_grant | revoked | expired`.
- У нас refresh есть, но policy обработки «мёртвого refresh token» пока проще.

**Что хотим сделать**
- Добавить явную классификацию ошибок refresh.
- Отдельно решить, нужно ли при `invalid_grant` очищать persisted credentials.

**Для чего это нужно**
- Чтобы не зациклиться на заведомо невалидном refresh token.
- Чтобы поведение state lifecycle было предсказуемым.

**Что это даёт**
- Более устойчивый OAuth lifecycle.
- Более понятную диагностику auth-проблем.
- Лучшую parity-совместимость с reference.

**Замечание**
- Это самый чувствительный пункт, потому что он уже влияет на lifecycle credential state, а не только на transport parity.

### 4. Тестовый контур parity

**Где расходимся**
- Базовые тесты у нас уже есть, но они не покрывают весь набор parity-расхождений.

**Что хотим сделать**
- Добавить тесты на MCP tool schema branch.
- Добавить тесты на unsafe и слишком длинный `call_id`.
- Добавить тесты на streaming delta без явных `id/name`.
- Добавить тесты на OAuth invalid-grant policy, если её примем.

**Для чего это нужно**
- Чтобы parity был подтверждён тестами, а не только ручным сравнением кода.

**Что это даёт**
- Безопасность изменений.
- Явную traceability между расхождением и фиксирующим тестом.

## Варианты объёма работ

### Вариант A. Консервативный
Включает:
- tool-call parity;
- streaming parity;
- тесты на эти изменения.

Не включает:
- изменение lifecycle policy для OAuth credentials.

**Когда выбирать**
- Если хотим сначала выровнять runtime transport semantics без изменения state lifecycle.

### Вариант B. Средний
Включает:
- всё из варианта A;
- OAuth error classification без агрессивной очистки credentials.

**Когда выбирать**
- Если хотим лучше различать классы auth ошибок, но не менять резко поведение persisted state.

### Вариант C. Полный parity
Включает:
- всё из варианта B;
- cleanup persisted credentials при явно невалидном refresh token по модели reference.

**Когда выбирать**
- Если цель — максимально близкое поведение к reference не только по transport, но и по lifecycle auth state.

## Предлагаемое решение

После обсуждения фиксируем целевой вектор как **вариант B+**:
- доводим runtime parity по tools и streaming;
- добавляем OAuth error classification;
- **не удаляем** credentials file;
- вместо удаления **помечаем аккаунт как auth-invalid в state**;
- router должен **игнорировать** такие аккаунты при rotation;
- оператору/пользователю явно рекомендуем повторно получить креды через [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py).

Это уже немного шире исходного варианта B, потому что затрагивает state и router behavior, но всё ещё безопаснее варианта C, где credentials удалялись бы автоматически.

## Архитектурная схема для invalid OAuth accounts

### Цель

Если refresh token для конкретного аккаунта стал невалидным, система должна:
1. распознать это как отдельный тип состояния;
2. не использовать такой аккаунт в runtime routing;
3. сохранить диагностическую информацию в state;
4. не уничтожать credentials автоматически;
5. подсказать оператору, что нужно повторно пройти bootstrap через [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py).

### Почему не надо удалять credentials

Автоматическое удаление файла credentials:
- ухудшает диагностику;
- ломает возможность понять, какой именно аккаунт отвалился;
- делает recovery менее прозрачным;
- слишком агрессивно смешивает detection и remediation.

Поэтому лучше разделить:
- **detection** — runtime обнаружил invalid grant;
- **state marking** — система пометила аккаунт как невалидный;
- **remediation** — человек пере-bootstrap-ит аккаунт.

### Предлагаемый state contract

Нужен отдельный runtime state для auth health аккаунта provider `openai-chatgpt`.

Рекомендуемая минимальная форма:

- `provider_id`
- `account_name`
- `credentials_path`
- `auth_status`
- `reason`
- `detected_at`
- `last_refresh_attempt_at`
- `recommended_action`

Где:
- `auth_status = valid | invalid_grant | refresh_failed_transient`
- `reason` хранит краткую machine-readable причину
- `recommended_action` для invalid account = `reauth_via_bootstrap_script`

### Где хранить state

Не в credentials JSON, а в runtime state рядом с остальными provider state артефактами.

Причина:
- credentials file — это источник OAuth секретов;
- auth health — это runtime operational state;
- смешивать их в одном файле нежелательно.

То есть архитектурно это должен быть тот же класс boundary, что и прочие runtime snapshots в [`STATE_DIR`](llm_agent_platform/config.py:30), а не модификация пользовательского credential артефакта.

### Как это должно влиять на router

#### Для `rounding`

Если аккаунт помечен как `invalid_grant`, router:
- исключает его из selectable pool;
- не пытается использовать его в rotation;
- продолжает работу на остальных аккаунтах группы.

Если все аккаунты в группе стали auth-invalid, это должен быть отдельный terminal state, отличный от quota exhaustion.
Ошибка - "all accounts auth-invalid".

#### Для `single`

Если active account помечен как `invalid_grant`, runtime не должен делать бесполезные refresh циклы.

Ожидаемое поведение:
- запрос быстро завершается auth error;
- в ошибке и логах есть указание на повторный bootstrap через [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py).

### Предлагаемые state transitions

- `unknown -> valid`
  - успешная загрузка и refresh credentials
- `valid -> refresh_failed_transient`
  - временная ошибка сети или upstream
- `valid -> invalid_grant`
  - детектирован revoked or expired or invalid refresh token
- `invalid_grant -> valid`
  - после успешного повторного bootstrap или успешного refresh с новыми credentials

### Provider capability rule for auth-health

Это состояние должно быть **capability-gated**, а не mandatory для всех providers.

Правило:
- если provider умеет надёжно различать permanent auth failure и transient auth failure, он пишет `auth` section в [`account_state.json`](llm_agent_platform/services/account_state_store.py:22)
- если provider этого пока не умеет, его `account_state.json` продолжает работать без `auth` section
- отсутствие `auth` section трактуется как `auth status = unknown`, а не как `invalid`
- router исключает аккаунт только при явном состоянии `invalid_grant`
- для providers без этой capability текущее поведение не меняется

Следствие:
- rollout можно делать сначала только для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1)
- schema account state должна поддерживать optional `auth` block
- router должен быть backward-compatible к старым state-файлам и к providers без auth-health detection

### Что считать invalid-grant сигналом

Как baseline использовать семантику из [`externel_projects/kilocode/src/integrations/openai-codex/oauth.ts`](externel_projects/kilocode/src/integrations/openai-codex/oauth.ts):
- `invalid_grant`
- `revoked`
- `expired`
- `invalid refresh`

Но важно разделять:
- **permanent auth failure** → маркируем account как invalid
- **transient failure** → не исключаем account из router навсегда

### Что нужно сделать в коде позже

1. В [`llm_agent_platform/auth/openai_chatgpt_oauth.py`](llm_agent_platform/auth/openai_chatgpt_oauth.py) добавить классификацию refresh ошибок.
2. Ввести запись auth-health state в runtime state boundary.
3. Научить [`llm_agent_platform/services/account_router.py`](llm_agent_platform/services/account_router.py) игнорировать auth-invalid accounts при выборе аккаунта.
4. Добавить явное различие между:
   - quota exhausted
   - cooldown
   - auth invalid
5. Добавить operator-facing logging и понятную ошибку с рекомендацией пере-bootstrap через [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py).
6. Добавить тесты на marking и router exclusion.

## Предлагаемый порядок выполнения

1. Довести parity по tool-call semantics.
2. Довести parity по streaming tool events.
3. Добавить OAuth invalid-grant classification.
4. Спроектировать и реализовать auth-health state для аккаунтов.
5. Подключить router exclusion для auth-invalid accounts.
6. Обновить тесты под tools, streaming и auth-invalid routing.

## Решение, которое предлагаю взять как baseline

Взять в работу такой baseline:
- **runtime parity по tools и streaming — да**
- **OAuth invalid-grant classification — да**
- **автоудаление credentials — нет**
- **mark account as invalid in state — да**
- **исключать invalid account из rotation — да**
- **рекомендовать reauth через [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py) — да**

Это даёт управляемую и наблюдаемую схему без агрессивного удаления пользовательских credential файлов.

## Решение, которое нужно подтвердить

Подтвердить, что для `openai-chatgpt` принимаем именно такую operational policy:
- invalid refresh token не удаляет credentials;
- invalid account маркируется в runtime state;
- router исключает его из selection pool;
- recovery выполняется только через явный reauth.

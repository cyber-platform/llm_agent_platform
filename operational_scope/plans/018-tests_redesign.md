Текущее состояние тестов показывало, что мы смешали уровни L2 (contract/mocked) и L3/L4 (integration/e2e с реальными токенами), из‑за чего тесты одновременно:
- пытаются проверить контракт стриминга/роутов, **но** внезапно требуют валидный `refresh_token` (что уже относится к проверке реальной OAuth-интеграции),
- и поэтому ломаются на фейковых кредах.

## 0) Принятое решение (фиксируем контракт)

1) **CI / дефолтный прогон**: держим только **L1+L2**.
   - Все тесты, которые проверяют shape/контракт API, должны быть **полностью mocked на границах OAuth и внешних вызовов**.
   - Никаких требований к `refresh_token` / реальным credentials по умолчанию.

2) **Будущее расширение**: добавляем **L4 e2e** тесты (opt-in), которые используют **реальные токены** и делают **реальные запросы** к самым дешёвым моделям каждого провайдера.
   - Эти тесты *не* должны быть обязательными в CI.

## 1) Что сейчас “требует реальные токены” (и почему)

### Qwen
Ветка Qwen в рантайме начинает с загрузки runtime-cred’ов через [`QwenCodeProvider.load_runtime_credentials()`](api/openai/providers/qwen_code.py:56).  
Если `_should_refresh_credentials` возвращает `True` (например, `last_used_at` отсутствует), вызывается [`refresh_qwen_credentials_file()`](auth/qwen_oauth.py:305), которая читает файл через [`read_qwen_credentials()`](auth/qwen_oauth.py:284) и **жёстко требует** `refresh_token`. Поэтому любые тесты, которые не замокали этот слой, автоматически становятся L3/L4.

### Gemini
Аналогично, “реальные токены” начинаются там, где вызывается [`get_gemini_access_token_from_file()`](auth/credentials.py:190) (refresh через Google OAuth). В L2 это нужно стабильно мокать.

### Почему “просто подложить fake credentials json” не работает
Потому что валидатор availability и OAuth-обвязка проверяют наличие refresh token:
- [`_credentials_has_refresh_token()`](auth/credentials.py:65)
- [`read_qwen_credentials()`](auth/qwen_oauth.py:284)

Если мы хотим **именно L2**, то такие проверки нужно изолировать моками на границе.

## 2) Отдельно: гипотеза, почему в реальном сервисе не появляется `last_used_at.json`
Запись `last_used_at` делается в [`_touch_last_used()`](api/openai/providers/qwen_code.py:175), а для streaming вызывается в `finally` у генератора [`QwenCodeProvider.stream_lines()`](api/openai/providers/qwen_code.py:131).

При этом стратегия для Qwen в стриминге может “досрочно” прекратить чтение апстрима, когда видит `[DONE]`, см. [`RotateOn429RoundingStrategy.stream()`](api/openai/strategies/rotate_on_429_rounding.py:169). Если consumer перестал итерировать генератор провайдера до исчерпания, `finally` может не сработать своевременно (генератор не закрыт), и `last_used_at.json` не пишется/пишется недетерминированно. Это **похоже на ваш симптом**: файлы exhausted пишутся из роутера синхронно (см. [`AccountStatePaths.account_dir`](services/account_state_store.py:23)), а `last_used_at` зависит от корректного закрытия генератора.

Архитектурный фикс тут обычно один из:
- гарантированно закрывать generator провайдера при `break` (через `closing()` / `try/finally iterator.close()`),
- или переносить запись `last_used_at` в более детерминированную точку (например, “после первого yield” или “после получения DONE” на уровне стратегии).

## 3) Предложение: разнести проверки по L1–L4 (coverage matrix)

Ниже — черновик требований (US) и тест-кейсов (TC), чтобы разнести уровни и не смешивать реальную OAuth-интеграцию с контрактами.

### US / TC (Given–When–Then)
- **US-AUTH-QWEN-01**: Qwen streaming после успешной сессии обновляет `last_used_at`.
  - **TC-AUTH-QWEN-01**
    - L2: mocked (без реальных токенов), проверяем факт записи `last_used_at` в FS через [`save_last_used_at()`](services/account_state_store.py:50)
    - L4: e2e (реальные токены + реальный запрос дешёвой модели), проверяем реальный файл на диске

- **US-AUTH-QWEN-02**: Логика idle-refresh (если давно не использовали — refresh, иначе read).
  - **TC-AUTH-QWEN-02**
    - L1: unit для [`_should_refresh_credentials()`](api/openai/providers/qwen_code.py:167) (без сети, без токенов)
    - L2: contract — проверка, что вызывается `read` vs `refresh` (моки), без реальных токенов
    - L3: integration — реальный refresh на реальных токенах (опционально/manual, потому что сеть/секреты)

- **US-AUTH-GEMINI-01**: Gemini токен refresh path работает.
  - **TC-AUTH-GEMINI-01**
    - L2: контракт пайплайна/роутов (всё замокано, включая [`get_gemini_access_token_from_file()`](auth/credentials.py:190))
    - L3/L4: реальные токены (manual/opt-in)

### Coverage matrix (черновик)
| TC | Что проверяем | L1 unit | L2 contract mocked | L3 integration real tokens | L4 e2e real request |
|---|---|---:|---:|---:|---:|
| TC-AUTH-QWEN-01 | запись `last_used_at` после stream |  | ✅ |  | ✅ |
| TC-AUTH-QWEN-02 | idle refresh decision | ✅ | ✅ | ✅ (opt-in) |  |
| TC-AUTH-GEMINI-01 | refresh/route path |  | ✅ | ✅ (opt-in) | ✅ (opt-in) |

## 4) Как это отразится на структуре тестов (архитектурно)
Чтобы не ломать CI и не требовать секретов всегда:
- L1+L2 остаются “по умолчанию” в `unittest discover`
- L3/L4 делаем **opt-in**: запускаются только при наличии env-флага и реальных секретов в `secrets/…` (как в каноне путей, см. [`AccountStatePaths.account_dir`](services/account_state_store.py:23))

Технически это можно реализовать через `@unittest.skipUnless(os.environ.get(...))` в отдельных `test_real_*.py` файлах, плюс отдельная suite-страница в [`docs/testing/test-map.md`](docs/testing/test-map.md:1), где будет явный runbook для real tokens.

## 5) Что именно “разнести” прямо сейчас (по текущим тестам)
В [`tests/test_openai_contract.py`](tests/test_openai_contract.py:1) есть тесты, которые сейчас фактически хотят L3 (потому что заходят в Qwen OAuth), но по смыслу они L2 (контракт стрима/файла `last_used_at`). Их нужно:
- либо сделать чистым L2: мокать границу OAuth (не “фейкать токены”, а именно мокать интеграцию),
- либо перенести в “real tokens suite” и запускать только opt-in.

В [`tests/test_refactor_p2_routes.py`](tests/test_refactor_p2_routes.py:1) smoke `/v1/models` — это L2 (контракт/смоук), и его правильно держать без реальных токенов.

Следующий шаг, который предлагаю зафиксировать после обсуждения: утвердить, какие TC относим к L2 (mock boundary), а какие — к L3/L4 (real tokens), и обновить карту тестирования в [`docs/testing/test-map.md`](docs/testing/test-map.md:1) отдельным разделом L3/L4 (manual/opt-in).

## 6) План: добавить L4 e2e real-tokens тесты (будущее)

Цель: иметь минимальный «дымовой» e2e для каждого провайдера, который:
- читает **реальные credentials** из `secrets/<provider_id>/accounts/<account>.json`;
- делает **один максимально дешёвый** запрос в модель;
- проверяет эффект уровня L4 (что реальные токены/интеграция/маршрутизация работают).

### 6.1) Общие требования к L4

- **Opt-in запуск**: `RUN_REAL_E2E=1`.
- **Модели по умолчанию** задаются через env и могут быть переопределены:
  - `E2E_GEMINI_MODEL` (default: `gemini-3-flash-preview-quota`)
  - `E2E_QWEN_MODEL` (default: `qwen-coder-model-quota`)
- **Минимальная стоимость**: короткий prompt (например, `"ping"`), `max_tokens=8` (или эквивалент), без tool-calling.
- **Стабильность**: тесты должны быть помечены как «manual/opt-in» и не запускаться в CI.

### 6.2) Предлагаемая структура файлов

- `llm_agent_platform/tests/test_real_e2e_gemini.py`
- `llm_agent_platform/tests/test_real_e2e_qwen.py`

Внутри:
- `@unittest.skipUnless(os.environ.get("RUN_REAL_E2E") == "1", "real e2e disabled")`
- дополнительные `skip` если нет нужных `secrets/...` файлов

### 6.3) Что именно проверять (минимальный контракт)

#### Gemini (L4)
- Вызов `/v1/chat/completions` с моделью `E2E_GEMINI_MODEL`.
- Ожидаем `200`.
- Проверяем, что ответ соответствует OpenAI shape (ключи `id/object/choices` и т.д.).

#### Qwen (L4)
- Вызов `/v1/chat/completions` с моделью `E2E_QWEN_MODEL`.
- Ожидаем `200`.
- Дополнительно (опционально) проверяем side-effect: запись `last_used_at.json` в `secrets/qwen_code/state/<account>/last_used_at.json`.

### 6.4) Runbook (локальный запуск)

```bash
RUN_REAL_E2E=1 \
E2E_GEMINI_MODEL=gemini-3-flash-preview-quota \
E2E_QWEN_MODEL=qwen-coder-model-quota \
uv run python -m unittest llm_agent_platform.tests.test_real_e2e_gemini llm_agent_platform.tests.test_real_e2e_qwen
```

### 6.5) Документация

После добавления L4 тестов:
- обновить индекс тестового контура: `docs/testing/test-map.md`
- добавить suite-страницу «Real Tokens / E2E» в `docs/testing/suites/`

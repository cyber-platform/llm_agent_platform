# Suite: OpenAI stream/non-stream contract

## Scope
- Проверка ответа `/v1/chat/completions` в non-stream формате.
- Проверка SSE потока с `stream_options.include_usage=true`.
- Проверка записи `last_used_at` для Qwen streaming.
- Проверка маппинга upstream-ошибки в OpenAI error shape.

## Test Level (L1–L4)
- L3 System (integration, real deps): контракт проверяется через реальный Flask endpoint прокси и реальные форматы ответа (JSON/SSE).

## Requirement Traceability
- Requirement: стабильный OpenAI-compatible контракт для Kilo Code.
- Canonical references:
  - Архитектура pipeline: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
  - Нормативные схемы ошибок: [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1)
- Script: [`test_openai_contract.py`](tests/test_openai_contract.py)

## Verification Command
- `uv run python -m unittest tests/test_openai_contract.py`

## Debug Methodology (usage in stream)

### Goal
- Диагностировать расхождения usage-токенов между non-stream и stream для OpenAI-compatible `/v1/chat/completions`.

### Step 1 — Baseline (non-stream)
- Выполнить non-stream запрос для каждого провайдера (`gemini`, `qwen`) и сохранить raw-ответ.
- Проверить поля `usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens`.

### Step 2 — Raw SSE capture
- Выполнить stream запрос с `stream_options.include_usage=true`.
- Сохранить полный SSE поток в debug-артефакт.
- Проверить наличие:
  - финального usage-чанка (`"choices": [], "usage": {...}`),
  - завершающего `data: [DONE]`.

### Step 3 — Upstream payload audit
- Проверить, что `stream_options` действительно прокидывается в upstream payload провайдера.
- Для `qwen` обязательно сверить, что `stream_options.include_usage=true` попадает в тело запроса.

### Step 4 — Proxy aggregation audit
- Проверить, что usage читается из входящих stream-чанков и аккумулируется.
- Проверить, что финальный usage-чанк отправляется клиенту до `data: [DONE]`.

### Step 5 — Success criteria
- В stream-артефакте присутствует ненулевой usage-чанк (если upstream usage вернул).
- UI KiloCode показывает usage-токены для stream-ответа без ручных workaround.

### Debug artifacts
- Директория: [`artifacts/debug/`](artifacts/debug/)
- Примеры файлов:
  - [`qwen_probe_stream_payload.json`](artifacts/debug/qwen_probe_stream_payload.json)
  - [`qwen_probe_stream.sse`](artifacts/debug/qwen_probe_stream.sse)
  - [`qwen_probe_response.json`](artifacts/debug/qwen_probe_response.json)

# Suite: OpenAI stream/non-stream contract

## Suite ID
- `TS-OPENAI-CONTRACT`

## Documentation roots
- `docs/testing/test-map.md`
- `docs/testing/traceability.md`
- `docs/testing/suites/openai-contract.md`

## Implementation roots
- `llm_agent_platform/tests/test_openai_contract.py`
- `llm_agent_platform/tests/test_openai_chatgpt_runtime.py`

## Search anchors
- `TS-OPENAI-CONTRACT`
- `test_openai_contract.py`
- `test_openai_chatgpt_runtime.py`
- `openai-chatgpt`

## Scope
- Проверка ответа provider-scoped `/chat/completions` в non-stream формате.
- Проверка SSE потока с `stream_options.include_usage=true`.
- Проверка записи `last_used_at` для Qwen streaming.
- Проверка private backend runtime adapter для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1), включая forced refresh retry и optional `ChatGPT-Account-Id`.
- Проверка маппинга upstream-ошибки в OpenAI error shape.
- Проверка того, что richer internal/admin quota taxonomy для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) не расширяет public `429` contract.
- Проверка streamed non-200 ошибки для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1): ошибка должна вернуться как OpenAI-compatible SSE event, без silent разрыва потока.
- Проверка strict OpenAI-compatible streaming parity для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1): partial `tool_calls[].function.arguments` не дублируются на `response.output_item.done`.
- Проверка reasoning parity для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1): reasoning stream отдается через `reasoning_text`, совместимый с KiloCode OpenAI-compatible parser.

## Test Level (L1–L4)
- L3 System (integration, real deps): контракт проверяется через реальный Flask endpoint прокси и реальные форматы ответа (JSON/SSE).

## Requirement Traceability
- Requirement: стабильный provider-centric OpenAI-compatible контракт.
- Rollout metadata:
  - suite anchor: `TS-OPENAI-CONTRACT`
  - future case anchors: `TC-OPENAI-CONTRACT-...`
- Canonical references:
  - Архитектура pipeline: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
  - Нормативные схемы ошибок: [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1)
  - Provider-specific quota boundary: [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- Script: [`llm_agent_platform/tests/test_openai_contract.py`](llm_agent_platform/tests/test_openai_contract.py:1), [`llm_agent_platform/tests/test_openai_chatgpt_runtime.py`](llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1)

## Verification Command
- `uv run python -m unittest llm_agent_platform/tests/test_openai_contract.py`
- `uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_runtime.py`

## Debug Methodology (usage in stream)

### Goal
- Диагностировать расхождения usage-токенов между non-stream и stream для provider-scoped OpenAI-compatible `/chat/completions`.

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

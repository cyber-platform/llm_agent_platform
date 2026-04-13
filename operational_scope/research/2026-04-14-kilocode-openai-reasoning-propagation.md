# Research: KiloCode OpenAI/Codex reasoning propagation and platform parity

Status: draft for implementation and parity analysis

## Scope

Это исследование фиксирует, как reasoning/рассуждения модели проходят через reference implementation в [`externel_projects/kilocode`](externel_projects/kilocode:1) для OpenAI/Codex-like providers и проверяет, передает ли reasoning текущая платформа в runtime provider [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1).

Цель документа — дать следующему агенту полную картину end-to-end:

- какие request fields включают reasoning на upstream;
- какие upstream response/events считаются reasoning-сигналами;
- как KiloCode мапит reasoning во внутренние parts и UI;
- как наша платформа нормализует private Responses backend в OpenAI-compatible `chat/completions` JSON/SSE;
- что именно доходит до клиента;
- какие потери и расхождения относительно reference behavior уже есть.

## Questions answered

1. Как KiloCode запрашивает reasoning у OpenAI/Codex provider.
2. Какие поля и stream events KiloCode поддерживает на ответе.
3. Как reasoning проходит через internal runtime KiloCode до session/UI.
4. Как reasoning проходит через наш provider adapter [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:1).
5. Передает ли наша платформа reasoning клиенту и в каком формате.
6. Что теряется относительно reference KiloCode.

## Sources reviewed

### Canonical project docs

- Provider canon: [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- Pipeline canon: [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
- Testing index: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- Contract suite: [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1)

### Reference KiloCode files

- Responses model implementation: [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1)
- OpenAI-compatible chat model implementation: [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:1)
- Provider transform layer: [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts`](externel_projects/kilocode/packages/opencode/src/provider/transform.ts:1)
- Session stream processor: [`externel_projects/kilocode/packages/opencode/src/session/processor.ts`](externel_projects/kilocode/packages/opencode/src/session/processor.ts:1)
- UI rendering of assistant/reasoning parts: [`externel_projects/kilocode/packages/ui/src/components/session-turn.tsx`](externel_projects/kilocode/packages/ui/src/components/session-turn.tsx:1)
- Webview message types: [`externel_projects/kilocode/packages/kilo-vscode/webview-ui/src/types/messages.ts`](externel_projects/kilocode/packages/kilo-vscode/webview-ui/src/types/messages.ts:1)

### Our platform files

- Provider adapter: [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:1)
- Related response shaper for other providers/reference contrast: [`services/backend/llm_agent_platform/api/openai/response_shaper.py`](services/backend/llm_agent_platform/api/openai/response_shaper.py:1)
- Related generic streaming helpers: [`services/backend/llm_agent_platform/api/openai/streaming.py`](services/backend/llm_agent_platform/api/openai/streaming.py:1)
- Runtime tests: [`services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py`](services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1)
- Request-policy task context: [`operational_scope/tasks/067-openai-chatgpt-reasoning-effort-adapter-integration.md`](operational_scope/tasks/067-openai-chatgpt-reasoning-effort-adapter-integration.md:1)

## Executive summary

Короткий вывод:

- KiloCode поддерживает reasoning как first-class internal content/stream primitive.
- Для OpenAI Responses KiloCode умеет запрашивать и разбирать reasoning summaries и encrypted reasoning metadata.
- Для OpenAI-compatible chat KiloCode умеет принимать reasoning через поле `reasoning_text` и SSE delta `reasoning_text`.
- Наша платформа действительно передает reasoning клиенту, но делает это в сжатом OpenAI-compatible surface через `reasoning_text`.
- Текущий runtime adapter не пробрасывает клиенту encrypted reasoning metadata и не сохраняет full-fidelity reasoning structure, которая есть в reference KiloCode.
- Кроме того, non-stream shaping в нашей платформе выглядит уже, чем reference parser KiloCode, и потенциально может пропускать часть top-level `reasoning` output items Responses API.

## Reference KiloCode: end-to-end reasoning flow

### 1. Request construction: KiloCode explicitly asks for reasoning

Для Responses API KiloCode не надеется на implicit behavior. Он явно конструирует payload с reasoning-specific settings.

Ключевые места:

- В [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:196) provider options парсятся через `openaiResponsesProviderOptionsSchema`.
- Schema поддерживает:
  - `reasoningEffort`
  - `reasoningSummary`
  - `include`
  - в том числе `include: ["reasoning.encrypted_content", ...]`
  - см. [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1691`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1691)
- При построении тела request KiloCode добавляет:
  - `reasoning: { effort, summary }`
  - `include`
  - см. [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:295`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:295)

Отдельно важно, что provider transform layer тоже знает о reasoning-конфигурации разных providers и для OpenAI/Codex-подобных путей добавляет `reasoningSummary: "auto"` и `include: ["reasoning.encrypted_content"]` в relevant provider options, см. [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:523`](externel_projects/kilocode/packages/opencode/src/provider/transform.ts:523), [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:555`](externel_projects/kilocode/packages/opencode/src/provider/transform.ts:555), [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:585`](externel_projects/kilocode/packages/opencode/src/provider/transform.ts:585), [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:853`](externel_projects/kilocode/packages/opencode/src/provider/transform.ts:853).

### 2. Non-stream response parsing: KiloCode preserves reasoning as its own content part

В non-stream Responses path KiloCode ожидает top-level `output[]` items разных типов, включая отдельный item `type: "reasoning"`.

Ключевые места:

- Response schema включает top-level item:
  - `type: "reasoning"`
  - `id`
  - `encrypted_content`
  - `summary: [{ type: "summary_text", text }]`
  - см. [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:478`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:478)
- При обходе `response.output` reasoning item превращается во внутренний `LanguageModelV2Content` part:
  - `type: "reasoning"`
  - `text: summary.text`
  - `providerMetadata.openai.itemId`
  - `providerMetadata.openai.reasoningEncryptedContent`
  - см. [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:520`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:520)

Практический смысл:

- reasoning не смешивается с обычным assistant text;
- encrypted reasoning metadata не теряется;
- последующие слои runtime могут отдельно хранить/рендерить reasoning parts.

### 3. Streaming response parsing: KiloCode has a dedicated reasoning event model

В stream path KiloCode поддерживает reasoning как отдельную stream-сущность, а не как текстовый хвост в `content`.

#### 3.1. Upstream events recognized

Stream schema и type guards явно поддерживают reasoning-related events:

- `response.output_item.added` с `item.type == "reasoning"` — [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1360`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1360)
- `response.output_item.done` с `item.type == "reasoning"` — [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1422`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1422)
- `response.reasoning_summary_part.added` — [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1504`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1504)
- `response.reasoning_summary_text.delta` — [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1510`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1510)

#### 3.2. Internal stream parts emitted

При старте reasoning item KiloCode эмитит `reasoning-start` с metadata, включая encrypted reasoning:

- см. [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:941`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:941)

При приходе summary text delta KiloCode эмитит `reasoning-delta`:

- см. [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1230`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1230)

При завершении reasoning item KiloCode эмитит `reasoning-end` и снова привязывает metadata:

- см. [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1101`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1101)

#### 3.3. Correlation semantics

KiloCode специально отслеживает reasoning не только по item id, но и по `output_index`, потому что Copilot/OpenAI-like backend может ротировать item ids между событиями:

- `activeReasoning` и `currentReasoningOutputIndex` объявлены в [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:818`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:818)

Это важное отличие от упрощенного proxy-адаптера: reference не просто forwards delta, а восстанавливает устойчивую reasoning structure поверх нестабильного upstream event stream.

### 4. OpenAI-compatible chat path: `reasoning_text` is a compatibility surface, not the full internal model

У KiloCode есть отдельный parser для OpenAI-compatible `chat/completions`. Именно этот parser важен для оценки совместимости нашей платформы.

#### 4.1. Non-stream chat parsing

В non-stream KiloCode ожидает в `choices[0].message` поля:

- `content`
- `reasoning_text`
- `reasoning_opaque`
- `tool_calls`

См. schema в [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:713`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:713).

Если приходит `message.reasoning_text`, KiloCode превращает его во внутренний content part `type: "reasoning"`:

- см. [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:231`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:231)

#### 4.2. Stream chat parsing

В streaming KiloCode ожидает `choices[0].delta.reasoning_text` и превращает это в internal stream lifecycle:

- `reasoning-start`
- `reasoning-delta`
- `reasoning-end`

См. [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:459`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:459).

Именно поэтому для клиента KiloCode-compatible `chat/completions` surface с полем `reasoning_text` уже достаточен, даже если underlying provider использует более богатую Responses semantics.

### 5. Session/runtime/UI: KiloCode keeps reasoning visible as a first-class message part

После provider parsing reasoning не теряется.

- Session processor принимает `reasoning-start`, `reasoning-delta`, `reasoning-end` и обновляет persistent session parts типа `reasoning`, см. [`externel_projects/kilocode/packages/opencode/src/session/processor.ts:65`](externel_projects/kilocode/packages/opencode/src/session/processor.ts:65).
- UI layer отдельно фильтрует parts `type == "reasoning"`, строит headings и решает видимость summary/thinking state, см. [`externel_projects/kilocode/packages/ui/src/components/session-turn.tsx:359`](externel_projects/kilocode/packages/ui/src/components/session-turn.tsx:359).
- Message types в webview тоже знают `type: "reasoning"`, см. [`externel_projects/kilocode/packages/kilo-vscode/webview-ui/src/types/messages.ts`](externel_projects/kilocode/packages/kilo-vscode/webview-ui/src/types/messages.ts:53).

Итого по reference:

- `reasoning_text` — это только compatibility transport surface для chat parser;
- внутри KiloCode reasoning живет как отдельный semantic part с metadata и stream lifecycle.

## Our platform: end-to-end reasoning flow

### 1. Request construction: platform asks upstream for reasoning summary

Текущий adapter [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:1) реально запрашивает reasoning у backend.

Ключевые места:

- `_map_reasoning_effort(...)` нормализует клиентское/политическое значение reasoning effort и пропускает не только `low|medium|high`, но вообще любое non-empty string, плюс алиасы `disable|disabled|off -> none`, см. [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:205`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:205).
- В `prepare_upstream(...)` adapter строит payload:
  - `model`
  - `stream`
  - `store: false`
  - `instructions`
  - `input`
  - при наличии reasoning effort: `reasoning: { effort, summary: "auto" }`
  - если effort не `none`: `include: ["reasoning.encrypted_content"]`
  - см. [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:555`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:555)

Это означает:

- upstream действительно просится вернуть reasoning summary;
- encrypted reasoning content тоже запрашивается у backend;
- adapter не делает synthetic disable reasoning, если значение задано.

Контекст решения зафиксирован и в operational task note [`operational_scope/tasks/067-openai-chatgpt-reasoning-effort-adapter-integration.md`](operational_scope/tasks/067-openai-chatgpt-reasoning-effort-adapter-integration.md:60).

### 2. Usage propagation: reasoning tokens are preserved

Даже если текст reasoning схлопывается, usage часть reasoning платформа сохраняет.

- `_usage_from_payload(...)` читает `usage.output_tokens_details.reasoning_tokens` и кладет это в OpenAI-compatible `completion_tokens_details.reasoning_tokens`, см. [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:216`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:216)

Это согласуется с reference KiloCode, где reasoning tokens тоже идут как отдельный usage field в:

- Responses path: [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:752`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:752)
- OpenAI-compatible chat path: [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:279`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:279)

### 3. Non-stream response shaping: platform emits `message.reasoning_text`

#### 3.1. Adapter behavior

Если upstream ответ уже является `chat.completion`, adapter просто подменяет `model` и возвращает payload как есть, см. [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:237`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:237).

Если upstream возвращает Responses-like payload, adapter выполняет custom shaping:

- собирает `output_text`
- пытается собрать `reasoning_text`
- собирает tool calls
- возвращает OpenAI-compatible JSON c `choices[0].message.reasoning_text`
- см. [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:244`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:244)

Ключевая строка результата:

- `message["reasoning_text"] = reasoning_text` — [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:282`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:282)

#### 3.2. Important limitation in current non-stream parser

В текущей реализации adapter собирает reasoning только из:

- `item.type == "message"`
- далее `content.type == "reasoning"`
- затем берет `content.get("summary", content.get("text", ""))`

См. [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:254`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:254).

Это уже, чем reference KiloCode, потому что reference Responses parser ожидает именно top-level output item:

- `output[].type == "reasoning"`
- `summary[]`

См. [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:478`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:478) и [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:518`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:518).

Следствие:

- если backend вернет reasoning только как top-level `type: "reasoning"`, а не вложенный `message.content[*].type == "reasoning"`, наш non-stream adapter может не донести reasoning до клиента;
- current adapter therefore confirms intent to forward reasoning, but not full parser parity with reference.

### 4. Streaming response shaping: platform emits SSE delta `reasoning_text`

#### 4.1. Stream event normalization

В stream path adapter переводит private backend events в OpenAI-compatible SSE chunks.

Reasoning-related event types, которые adapter понимает напрямую:

- `response.reasoning.delta`
- `response.reasoning_text.delta`
- `response.reasoning_summary.delta`
- `response.reasoning_summary_text.delta`

См. [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:333`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:333).

При их получении adapter возвращает SSE chunk вида:

```json
{
  "choices": [
    {
      "delta": {
        "reasoning_text": "..."
      }
    }
  ]
}
```

Это строится через `_stream_chunk(raw_model, {'reasoning_text': delta})` в [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:344`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:344).

#### 4.2. Fallback extraction from final items

Если stream reasoning не пришел в delta-виде, adapter все равно пытается достать reasoning из финальных output items:

- `response.output_item.done` с `item.type == "reasoning"` и `item["text"]` — [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:409`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:409)
- `response.output_item.done` с `item.type == "message"`, затем `content.type == "reasoning"`, и берется `summary` или `text` — [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:416`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:416)

То есть stream path по reasoning выглядит более устойчивым, чем non-stream path.

#### 4.3. Stream state semantics

Adapter отслеживает `reasoning_delta_seen`, чтобы не дублировать reasoning при fallback extraction, см. [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:698`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:698).

Это решает задачу anti-duplication, но все еще существенно проще reference KiloCode, где есть:

- correlation по `output_index`
- multi-part reasoning lifecycle
- attachment of encrypted reasoning metadata

См. reference state machine в [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:818`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:818).

### 5. Test evidence: platform intentionally exposes `reasoning_text`

Контракт не только реализован, но и явно проверен тестом.

Ключевой runtime test:

- [`services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1184`](services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1184)

Что проверяет тест:

- backend stream присылает `data: {"type":"response.reasoning_text.delta","delta":"thinking"}`
- endpoint `/openai-chatgpt/v1/chat/completions` возвращает клиенту SSE с `"reasoning_text": "thinking"`
- поле `reasoning_content` не используется

Ключевые assertions:

- [`services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1239`](services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1239)
- [`services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1240`](services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1240)

Это полностью согласуется с docs canon:

- `Streaming adapter обязан ... с reasoning через reasoning_text` — [`docs/providers/openai-chatgpt.md:147`](docs/providers/openai-chatgpt.md:147)
- `reasoning stream отдается через reasoning_text, совместимый с KiloCode OpenAI-compatible parser` — [`docs/testing/suites/openai-contract.md:31`](docs/testing/suites/openai-contract.md:31)

## Field-by-field comparison

### Request side

| Concern | KiloCode reference | Our platform |
| --- | --- | --- |
| Reasoning effort | `reasoning.effort` in Responses body, see [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:298`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:298) | `payload["reasoning"]["effort"]`, see [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:580`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:580) |
| Reasoning summary mode | `reasoning.summary`, see [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:302`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:302) | `payload["reasoning"]["summary"] = "auto"`, see [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:582`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:582) |
| Request encrypted reasoning | `include: ["reasoning.encrypted_content"]`, see [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1692`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1692) | `payload["include"] = ["reasoning.encrypted_content"]`, see [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:579`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:579) |

### Response side

| Concern | KiloCode reference | Our platform |
| --- | --- | --- |
| Non-stream reasoning surface to client/parser | internal `type: "reasoning"` part in Responses path; `message.reasoning_text` in OpenAI-compatible chat path | OpenAI-compatible `choices[0].message.reasoning_text` |
| Stream reasoning surface to client/parser | internal `reasoning-start/delta/end`; OpenAI-compatible parser accepts `delta.reasoning_text` | OpenAI-compatible `choices[0].delta.reasoning_text` |
| Encrypted reasoning metadata | preserved in `providerMetadata.openai.reasoningEncryptedContent` | requested upstream, but not exposed to client |
| Item correlation | `output_index` and canonical item ids tracked | not tracked beyond simple dedupe flag |
| Multi-summary support | yes, via `summary_index` handling | no explicit multi-part model |

## Supported upstream reasoning signals

### In KiloCode reference

#### Responses non-stream items

- `output[].type == "reasoning"`
- `encrypted_content`
- `summary[].type == "summary_text"`
- `summary[].text`

See [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:478`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:478).

#### Responses stream events

- `response.output_item.added`
- `response.output_item.done`
- `response.reasoning_summary_part.added`
- `response.reasoning_summary_text.delta`

See [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1517`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1517).

#### OpenAI-compatible chat events/fields

- `message.reasoning_text`
- `message.reasoning_opaque`
- `delta.reasoning_text`
- `delta.reasoning_opaque`

See [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:713`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:713) and [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:745`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:745).

### In our platform adapter

#### Request-side fields

- `reasoning.effort`
- `reasoning.summary`
- `include = ["reasoning.encrypted_content"]`

See [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:577`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:577).

#### Stream-side incoming events recognized

- `response.reasoning.delta`
- `response.reasoning_text.delta`
- `response.reasoning_summary.delta`
- `response.reasoning_summary_text.delta`
- fallback `response.output_item.done` with `item.type == "reasoning"`
- fallback `response.output_item.done` with `item.type == "message"` and `content.type == "reasoning"`

See [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:333`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:333) and [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:391`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:391).

#### Client-visible fields emitted

- non-stream: `choices[0].message.reasoning_text`
- stream: `choices[0].delta.reasoning_text`
- usage: `usage.completion_tokens_details.reasoning_tokens`

See [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:282`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:282), [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:344`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:344), [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:230`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:230).

## Main conclusion: does our platform forward reasoning?

Да, передает.

Точное утверждение:

- текущая платформа для provider [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) forwards reasoning от private OpenAI/Codex-like backend в публичный OpenAI-compatible API contract;
- reasoning доходит до клиента не как internal part object и не как encrypted reasoning payload, а как plain compatibility field `reasoning_text`;
- это сделано намеренно и соответствует declared project contract, ориентированному на совместимость с KiloCode OpenAI-compatible parser.

### What is definitely working today

- Request path просит reasoning у upstream.
- Stream path forwards reasoning deltas в `delta.reasoning_text`.
- Usage path forwards `reasoning_tokens`.
- Contract закреплен тестами и docs.

### What is not preserved today

- `reasoning.encrypted_content` не доходит до клиента.
- `providerMetadata.openai.itemId` не доходит до клиента.
- нет explicit lifecycle `reasoning-start/reasoning-delta/reasoning-end` на public API boundary.
- нет full-fidelity representation multiple reasoning summary parts.
- non-stream parser потенциально теряет top-level `output[].type == "reasoning"` items.

## Detailed parity assessment against KiloCode

### Parity achieved

1. **Request intent parity**
   - Обе системы явно включают reasoning effort/summary в upstream request.
   - Обе системы умеют просить `reasoning.encrypted_content`.

2. **Client compatibility parity**
   - KiloCode chat parser понимает `reasoning_text`.
   - Наша платформа возвращает `reasoning_text`.
   - Следовательно, KiloCode как OpenAI-compatible client может прочитать reasoning из нашей платформы.

3. **Usage parity**
   - `reasoning_tokens` forwarded в usage details.

### Parity missing

1. **Responses fidelity parity**
   - KiloCode умеет полноценно читать top-level Responses reasoning items.
   - Наша платформа преобразует rich Responses model в упрощенный `reasoning_text`.

2. **Metadata parity**
   - KiloCode сохраняет `reasoningEncryptedContent` в provider metadata.
   - Наша платформа metadata отбрасывает.

3. **Correlation parity**
   - KiloCode имеет устойчивую state machine по `output_index`.
   - Наша платформа использует только `reasoning_delta_seen` и fallback extraction.

4. **Non-stream parser parity**
   - В KiloCode parser соответствует documented Responses item shape.
   - В нашей платформе parser выглядит более ad-hoc и уже.

## Concrete risks and gaps

### Risk 1. Non-stream reasoning may be partially lost

Если upstream вернет reasoning только в top-level item:

- `output[].type == "reasoning"`
- `summary[]`

то current `_shape_non_stream_response(...)` может не извлечь его, потому что ищет reasoning внутри `message.content[]`, а не в top-level item.

Relevant files:

- Our parser: [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:248`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:248)
- Reference parser: [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:518`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:518)

### Risk 2. Encrypted reasoning is requested but discarded

Платформа делает request `include: ["reasoning.encrypted_content"]`, но в downstream contract это содержимое не появляется.

Relevant files:

- Request include: [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:579`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:579)
- Reference metadata preservation: [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:531`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:531)

Это не обязательно bug, если canonical public contract действительно должен быть minimal. Но это осознанная потеря fidelity.

### Risk 3. No way to reconstruct reasoning segmentation downstream

В KiloCode reasoning может быть multi-part и имеет lifecycle, полезный для rich UI/state.

В нашей платформе downstream consumer видит только поток plain text fragments в `reasoning_text`.

Relevant files:

- KiloCode multi-part reasoning: [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1211`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1211)
- Our flattened stream: [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:344`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:344)

## Recommended next steps

### 1. Fix non-stream parser parity first

Приоритетный improvement — привести `_shape_non_stream_response(...)` к реальному Responses shape и support top-level `type == "reasoning"` items с `summary[]`.

Основная цель:

- non-stream contract должен быть не уже, чем stream contract;
- reasoning не должен зависеть от случайной nested shape backend payload.

Primary target file:

- [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:237)

### 2. Decide whether encrypted reasoning metadata belongs in public contract

Нужно отдельное архитектурное решение:

- либо `reasoning.encrypted_content` остается internal-only и не выходит за public API;
- либо вводится optional OpenAI-compatible extension field для advanced clients.

Без этого сейчас есть asymmetry: поле upstream запрашивается, но downstream contract его никогда не показывает.

### 3. Keep `reasoning_text` as compatibility baseline

Независимо от richer extensions, `reasoning_text` нужно сохранить как baseline contract, потому что:

- он уже зафиксирован в [`docs/providers/openai-chatgpt.md:147`](docs/providers/openai-chatgpt.md:147);
- он уже протестирован в [`services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1184`](services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1184);
- он совместим с parser logic KiloCode в [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:459`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:459).

## Final verdict

Полная формулировка вывода:

- Reference KiloCode реализует reasoning как first-class internal semantic stream/content model с поддержкой OpenAI Responses reasoning items, reasoning summary stream events, encrypted reasoning metadata и UI/session rendering отдельных reasoning parts.
- Наша платформа для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) действительно forwards reasoning от OpenAI/Codex backend клиенту.
- Forwarding выполняется через OpenAI-compatible compatibility field `reasoning_text`:
  - non-stream: `choices[0].message.reasoning_text`
  - stream: `choices[0].delta.reasoning_text`
- Этот contract совместим с KiloCode как с OpenAI-compatible client/parser.
- При этом текущая платформа не обеспечивает full-fidelity parity с reference KiloCode, потому что:
  - encrypted reasoning metadata отбрасывается;
  - rich reasoning lifecycle не экспонируется downstream;
  - non-stream parser потенциально уже reference parser и требует доработки для полного соответствия Responses shape.

## Quick reference map

### Most important KiloCode references

- Request/body reasoning settings: [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:295`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:295)
- Responses reasoning item schema: [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:478`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:478)
- Non-stream reasoning mapping: [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:520`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:520)
- Stream reasoning start: [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:949`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:949)
- Stream reasoning delta: [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1235`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1235)
- Stream reasoning end: [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1105`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/responses/openai-responses-language-model.ts:1105)
- OpenAI-compatible parser for `reasoning_text`: [`externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:231`](externel_projects/kilocode/packages/opencode/src/provider/sdk/copilot/chat/openai-compatible-chat-language-model.ts:231)
- Session reasoning persistence: [`externel_projects/kilocode/packages/opencode/src/session/processor.ts:65`](externel_projects/kilocode/packages/opencode/src/session/processor.ts:65)
- UI reasoning rendering: [`externel_projects/kilocode/packages/ui/src/components/session-turn.tsx:359`](externel_projects/kilocode/packages/ui/src/components/session-turn.tsx:359)

### Most important platform references

- Request reasoning payload: [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:577`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:577)
- Non-stream shaping entrypoint: [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:237`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:237)
- Non-stream `reasoning_text` emission: [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:282`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:282)
- Stream reasoning event mapping: [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:333`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:333)
- Stream `reasoning_text` SSE emission: [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:344`](services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py:344)
- Runtime test proving reasoning exposure: [`services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1184`](services/backend/llm_agent_platform/tests/test_openai_chatgpt_runtime.py:1184)
- Canonical doc requirement: [`docs/providers/openai-chatgpt.md:147`](docs/providers/openai-chatgpt.md:147)
- Canonical test suite requirement: [`docs/testing/suites/openai-contract.md:31`](docs/testing/suites/openai-contract.md:31)

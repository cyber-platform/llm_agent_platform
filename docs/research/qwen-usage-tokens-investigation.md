# Расследование: Почему для Qwen в UI отображается 0 usage токенов

## Дата
2026-03-02

## Проблема
В webview KiloCode для моделей Qwen отображается 0 использованных токенов (usage tokens), несмотря на то что API возвращает usage данные.

## Ключевые находки

### 1. Прокси (gemini_openai_proxy) корректно возвращает usage

**Non-streaming ответ** (`qwen_probe_response.json`):
```json
{
    "usage": {
        "completion_tokens": 537,
        "prompt_tokens": 16,
        "total_tokens": 553
    }
}
```

**Stream fallback** при ошибке quota (`qwen_probe_stream.sse`):
```
data: {"error": {"message": "429:{...}", "type": "stream_exception"}}
```

В потоковом режиме прокси **не отправляет** usage чанки в конце потока — только текстовые чанки и финальный `[DONE]`.

### 2. QwenCodeHandler (KiloCode) корректно обрабатывает usage

**Файл:** `kilocode/src/api/providers/qwen-code.ts:313-319`

```typescript
if (apiChunk.usage) {
    yield {
        type: "usage",
        inputTokens: apiChunk.usage.prompt_tokens || 0,
        outputTokens: apiChunk.usage.completion_tokens || 0,
    }
}
```

**Проблема:** здесь не передаётся `total_tokens`, только `inputTokens` и `outputTokens`.

### 3. UI ожидает полные usage данные

**ChatRow.tsx** (`kilocode/webview-ui/src/components/chat/ChatRow.tsx:268-274`):
```typescript
const [cost, usageMissing, inferenceProvider, ...] = useMemo(() => {
    if (message.text !== null && message.say === "api_req_started") {
        const info = JSON.parse(message.text)
        return [
            info?.cost,
            info?.usageMissing,  // ← Флаг отсутствия usage!
            info?.inferenceProvider,
            ...
        ]
    }
}, [message.text, message.say])
```

В UI есть флаг `usageMissing`, который показывается когда usage не был получен.

### 4. Task собирает usage из потока

**Task.ts** (`kilocode/src/core/task/Task.ts:3048-3052`):
```typescript
case "usage":
    inputTokens += chunk.inputTokens
    outputTokens += chunk.outputTokens
    // ... обновление UI
```

## Корень проблемы

### Потоковый режим (streaming)

В потоковом режиме прокси **не отправляет usage чанки** в формате OpenAI-compatible SSE. Вместо этого:

1. Прокси отправляет текстовые чанки через `stream_generate_lines_from_url()`
2. В конце отправляет `data: [DONE]\n\n`
3. Usage данные **не включены** в поток!

**Код прокси** (`api/openai/routes.py:451-486`):
```python
for line in lines:
    if is_qwen_quota_mode and line.startswith("data: "):
        # ... обработка чанков ...
        openai_chunk = _openai_chunk_from_qwen(parsed, raw_model)
        yield f"data: {json.dumps(sanitize_data(openai_chunk), ensure_ascii=False)}\n\n"
        
        usage = parsed.get("usage")
        if usage:
            usage_accumulated["prompt_tokens"] = usage.get("prompt_tokens", 0)
            # ... накопление usage ...
```

Usage данные **извлекаются из ответа Qwen API**, но **не отправляются клиенту** в виде отдельного usage чанка.

## Решение

### Вариант 1: Добавить usage чанк в конце потока (рекомендуется)

В `api/openai/routes.py` в потоковом режиме для Qwen нужно добавить отправку usage чанка перед `[DONE]`:

```python
# После цикла for line in lines:
if include_usage and (usage_accumulated["prompt_tokens"] > 0 or usage_accumulated["completion_tokens"] > 0):
    usage_chunk = {
        "id": f"chatcmpl-{int(time.time())}",
        "object": "chat.completion.chunk",
        "created": int(time.time()),
        "model": raw_model,
        "choices": [],
        "usage": usage_accumulated
    }
    yield f"data: {json.dumps(usage_chunk)}\n\n"

yield "data: [DONE]\n\n"
```

### Вариант 2: Использовать non-streaming режим

В `qwen-code.ts` можно отключить streaming для Qwen:
```typescript
stream: false,  // вместо true
// убрать stream_options
```

Тогда usage будет возвращаться в полном ответе.

### Вариант 3: Доработать qwen-code handler

Добавить фоновый запрос для получения usage после завершения потока (не рекомендуется из-за сложности).

## Проверка гипотезы

Проверить, что Qwen API действительно возвращает usage в потоке:

```bash
curl -N https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer $QWEN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-coder-plus",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true,
    "stream_options": {"include_usage": true}
  }'
```

Если Qwen API **не поддерживает** `include_usage` в потоке, то необходимо реализовать **Вариант 1** на стороне прокси.

## Ссылки

- Прокси: `api/openai/routes.py` — потоковая обработка Qwen
- KiloCode handler: `kilocode/src/api/providers/qwen-code.ts:313-319`
- UI отображение: `kilocode/webview-ui/src/components/chat/ChatRow.tsx:268-274`
- Task обработка: `kilocode/src/core/task/Task.ts:3048-3052`

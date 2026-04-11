# LLM API protocol taxonomy

## Назначение

Этот документ фиксирует каноническую терминологию для стандартов API-взаимодействия с LLM в контексте `llm_agent_platform`.

## Канонический общий термин

Общий термин: [`LLM API protocol`](./terms/project/terms/llm-api-protocol.md).

Под ним понимается стандарт API-взаимодействия с LLM: request shape, response shape, streaming semantics, tool-calling envelope и error boundary.

## Каноническая классификация

### `OpenAI API`

- vendor-specific API protocol от `OpenAI`;
- не является публичным API платформы как ownership boundary.

### [`OpenAI-compatible API`](./terms/project/terms/openai-compatible-api.md)

- protocol family, совместимая по shape с `OpenAI API`;
- основной public `LLM API protocol`, который экспонирует `llm_agent_platform`.

### `Anthropic API`

- vendor-specific API protocol от `Anthropic`.

### `Google Gemini API`

- vendor-specific API protocol от `Google`;
- используется как пример vendor-specific upstream protocol, к которому может адаптироваться [`provider-implementation`](./terms/project/terms/provider-implementation.md).

## Архитектурное правило для проекта

- наружу платформа в первую очередь предоставляет [`OpenAI-compatible API`](./terms/project/terms/openai-compatible-api.md);
- внутри runtime [`provider-implementation`](./terms/project/terms/provider-implementation.md) может адаптировать этот public protocol к vendor-specific upstream protocol;
- для `gemini` это означает: client-facing side остается `OpenAI-compatible API`, а upstream side может использовать `Google Gemini API`.

## Что не нужно смешивать

- `LLM provider` — это внешняя system boundary, а не protocol;
- `provider implementation` — это внутренняя реализация адаптера, а не public API standard;
- `OpenAI API` и `OpenAI-compatible API` — не одно и то же.

## Related documents

- [`llm-api-protocol`](./terms/project/terms/llm-api-protocol.md)
- [`openai-compatible-api`](./terms/project/terms/openai-compatible-api.md)
- [`provider-implementation`](./terms/project/terms/provider-implementation.md)
- [`llm-provider`](./terms/project/terms/llm-provider.md)

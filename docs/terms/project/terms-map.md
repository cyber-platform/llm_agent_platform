# Карта терминов

## Назначение

Этот документ является scoped terminology entry point для project-specific терминов `llm_agent_platform`.

Он нужен как краткий glossary entry point для человека и агента с progressive disclosure от короткого определения к отдельной term page.

## Как пользоваться этим файлом

Рекомендуемый маршрут такой:

1. прочитать короткое определение здесь;
2. если у термина есть отдельная страница, открыть ее только при необходимости;
3. вернуться к исходному архитектурному документу.

## Канонический реестр терминов

| Термин | Краткое определение | Детальная страница |
| --- | --- | --- |
| LLM API protocol | Общий термин для стандарта API-взаимодействия с LLM: request/response format, streaming semantics, tool-calling envelope и error boundary. | [`llm-api-protocol`](./terms/llm-api-protocol.md) |
| OpenAI-compatible API | Основной public [`LLM API protocol`](./terms/llm-api-protocol.md) платформы, совместимый с `OpenAI API`, но не равный vendor-specific `OpenAI API`. | [`openai-compatible-api`](./terms/openai-compatible-api.md) |
| hydrate | Восстановить in-memory state из persisted state. | [`hydrate`](./terms/hydrate.md) |
| persist | Сохранить runtime state из памяти в устойчивое хранилище. | [`persist`](./terms/persist.md) |
| RBAC | Модель авторизации, в которой доступ к страницам, действиям и операциям определяется ролью пользователя. | [`rbac`](./terms/rbac.md) |
| LLM Vendor | Компания или внешний владелец LLM-платформ и model access surfaces. Один `LLM Vendor` может предоставлять несколько разных `LLM provider`. | [`llm-vendor`](./terms/llm-vendor.md) |
| LLM provider | Внешняя система доступа к LLM-моделям со своим catalog, auth-mechanism, quota semantics и usage policy. | [`llm-provider`](./terms/llm-provider.md) |
| abstract provider | Внутренняя абстрактная сущность платформы, представляющая интеграцию с конкретным `LLM provider`. | [`abstract-provider`](./terms/abstract-provider.md) |
| provider implementation | Конкретная реализация `abstract provider` в коде платформы, которая адаптирует platform public protocol к vendor-specific upstream API конкретного `LLM provider`. | [`provider-implementation`](./terms/provider-implementation.md) |

## Политика обновления

Обновляй эту карту, если:

- новый повторяющийся термин появился в двух и более документах;
- термин изменил смысл или scope;
- появилась или была удалена отдельная term page.

Этот файл является терминологической точкой входа для человека и агента внутри `project` scope.

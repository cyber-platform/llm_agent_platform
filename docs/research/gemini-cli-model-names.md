# Названия моделей в gemini-cli

## Обзор

Документ описывает все названия моделей и алиасы, используемые в gemini-cli для взаимодействия с Gemini API.

## Конкретные названия моделей (Concrete Models)

| Модель | Описание |
|--------|----------|
| `gemini-3-pro-preview` | Gemini 3 Pro Preview |
| `gemini-3-flash-preview` | Gemini 3 Flash Preview |
| `gemini-2.5-pro` | Gemini 2.5 Pro |
| `gemini-2.5-flash` | Gemini 2.5 Flash |
| `gemini-2.5-flash-lite` | Gemini 2.5 Flash Lite |
| `gemini-3.1-pro-preview` | Gemini 3.1 Pro Preview |
| `gemini-3.1-pro-preview-customtools` | Gemini 3.1 Pro Preview Custom Tools |

Источник: [`externel_projects/gemini-cli/packages/core/src/config/models.ts`](../../../externel_projects/gemini-cli/packages/core/src/config/models.ts:7-24)

## Пользовательские алиасы (User Aliases)

| Алиас | Резолвится в | Описание |
|-------|-------------|----------|
| `auto` | `gemini-3-pro-preview` | Автоматический выбор модели |
| `pro` | `gemini-3-pro-preview` | Pro модель |
| `flash` | `gemini-3-flash-preview` | Flash модель |
| `flash-lite` | `gemini-2.5-flash-lite` | Flash Lite модель |
| `auto-gemini-3` | `gemini-3-pro-preview` | Автоматический выбор для Gemini 3 |
| `auto-gemini-2.5` | `gemini-2.5-pro` | Автоматический выбор для Gemini 2.5 |

Источник: [`externel_projects/gemini-cli/packages/core/src/config/models.ts`](../../../externel_projects/gemini-cli/packages/core/src/config/models.ts:26-33)

## Внутренние алиасы (Internal Aliases)

### Базовые конфигурации

| Алиас | Модель | Назначение |
|-------|--------|------------|
| `base` | - | Базовый конфиг (температура 0) |
| `chat-base` | - | Базовый конфиг для чата |
| `chat-base-2.5` | - | Базовый конфиг для Gemini 2.5 |
| `chat-base-3` | - | Базовый конфиг для Gemini 3 |
| `gemini-2.5-flash-base` | `gemini-2.5-flash` | Базовый конфиг для Gemini 2.5 Flash |
| `gemini-3-flash-base` | `gemini-3-flash-preview` | Базовый конфиг для Gemini 3 Flash |

Источник: [`externel_projects/gemini-cli/packages/core/src/config/defaultModelConfigs.ts`](../../../externel_projects/gemini-cli/packages/core/src/config/defaultModelConfigs.ts:16-104)

### Специализированные алиасы

| Алиас | Модель | Назначение |
|-------|--------|------------|
| `classifier` | `gemini-2.5-flash-lite` | Классификатор |
| `prompt-completion` | `gemini-2.5-flash-lite` | Завершение промпта |
| `fast-ack-helper` | `gemini-2.5-flash-lite` | Быстрый помощник |
| `edit-corrector` | `gemini-2.5-flash-lite` | Корректор редактирования |
| `summarizer-default` | `gemini-2.5-flash-lite` | Стандартный суммаризатор |
| `summarizer-shell` | `gemini-2.5-flash-lite` | Shell суммаризатор |
| `web-search` | `gemini-3-flash-preview` | Веб-поиск |
| `web-fetch` | `gemini-3-flash-preview` | Веб-загрузка |
| `web-fetch-fallback` | `gemini-3-flash-preview` | Запасной вариант веб-загрузки |
| `loop-detection` | `gemini-3-flash-preview` | Обнаружение циклов |
| `loop-detection-double-check` | `gemini-3-pro-preview` | Двойная проверка циклов |
| `llm-edit-fixer` | `gemini-3-flash-preview` | Исправитель редактирования LLM |
| `next-speaker-checker` | `gemini-3-flash-preview` | Проверка следующего спикера |

Источник: [`externel_projects/gemini-cli/packages/core/src/config/defaultModelConfigs.ts`](../../../externel_projects/gemini-cli/packages/core/src/config/defaultModelConfigs.ts:105-210)

### Алиасы сжатия чата

| Алиас | Модель | Назначение |
|-------|--------|------------|
| `chat-compression-3-pro` | `gemini-3-pro-preview` | Сжатие чата для Gemini 3 Pro |
| `chat-compression-3-flash` | `gemini-3-flash-preview` | Сжатие чата для Gemini 3 Flash |
| `chat-compression-2.5-pro` | `gemini-2.5-pro` | Сжатие чата для Gemini 2.5 Pro |
| `chat-compression-2.5-flash` | `gemini-2.5-flash` | Сжатие чата для Gemini 2.5 Flash |
| `chat-compression-2.5-flash-lite` | `gemini-2.5-flash-lite` | Сжатие чата для Gemini 2.5 Flash Lite |
| `chat-compression-default` | `gemini-3-pro-preview` | Сжатие чата по умолчанию |

Источник: [`externel_projects/gemini-cli/packages/core/src/config/defaultModelConfigs.ts`](../../../externel_projects/gemini-cli/packages/core/src/config/defaultModelConfigs.ts:211-240)

## Механизм работы

### 1. Разрешение алиасов

Пользовательский алиас разрешается через функцию [`resolveModel()`](../../../externel_projects/gemini-cli/packages/core/src/config/models.ts:48):

```typescript
export function resolveModel(
  requestedModel: string,
  useGemini3_1: boolean = false,
  useCustomToolModel: boolean = false,
): string {
  switch (requestedModel) {
    case PREVIEW_GEMINI_MODEL:
    case PREVIEW_GEMINI_MODEL_AUTO:
    case GEMINI_MODEL_ALIAS_AUTO:
    case GEMINI_MODEL_ALIAS_PRO: {
      if (useGemini3_1) {
        return useCustomToolModel
          ? PREVIEW_GEMINI_3_1_CUSTOM_TOOLS_MODEL
          : PREVIEW_GEMINI_3_1_MODEL;
      }
      return PREVIEW_GEMINI_MODEL;
    }
    case DEFAULT_GEMINI_MODEL_AUTO: {
      return DEFAULT_GEMINI_MODEL;
    }
    case GEMINI_MODEL_ALIAS_FLASH: {
      return PREVIEW_GEMINI_FLASH_MODEL;
    }
    case GEMINI_MODEL_ALIAS_FLASH_LITE: {
      return DEFAULT_GEMINI_FLASH_LITE_MODEL;
    }
    default: {
      return requestedModel;
    }
  }
}
```

### 2. Преобразование для сжатия чата

Функция [`modelStringToModelConfigAlias()`](../../../externel_projects/gemini-cli/packages/core/src/services/chatCompressionService.ts:101) преобразует название модели в алиас конфигурации:

```typescript
export function modelStringToModelConfigAlias(model: string): string {
  switch (model) {
    case PREVIEW_GEMINI_MODEL:
    case PREVIEW_GEMINI_3_1_MODEL:
      return 'chat-compression-3-pro';
    case PREVIEW_GEMINI_FLASH_MODEL:
      return 'chat-compression-3-flash';
    case DEFAULT_GEMINI_MODEL:
      return 'chat-compression-2.5-pro';
    case DEFAULT_GEMINI_FLASH_MODEL:
      return 'chat-compression-2.5-flash';
    case DEFAULT_GEMINI_FLASH_LITE_MODEL:
      return 'chat-compression-2.5-flash-lite';
    default:
      return 'chat-compression-default';
  }
}
```

### 3. Отправка запроса к Gemini API

Запрос к Gemini API формируется в [`converter.ts`](../../../externel_projects/gemini-cli/packages/core/src/code_assist/converter.ts:119):

```typescript
export function toGenerateContentRequest(
  req: GenerateContentParameters,
  userPromptId: string,
  project?: string,
  sessionId?: string,
): CAGenerateContentRequest {
  return {
    model: req.model,  // Конкретное название модели
    project,
    user_prompt_id: userPromptId,
    request: toVertexGenerateContentRequest(req, sessionId),
  };
}
```

## Источники

1. **Модели и алиасы**: [`externel_projects/gemini-cli/packages/core/src/config/models.ts`](../../../externel_projects/gemini-cli/packages/core/src/config/models.ts:1)
2. **Конфигурации по умолчанию**: [`externel_projects/gemini-cli/packages/core/src/config/defaultModelConfigs.ts`](../../../externel_projects/gemini-cli/packages/core/src/config/defaultModelConfigs.ts:1)
3. **Сжатие чата**: [`externel_projects/gemini-cli/packages/core/src/services/chatCompressionService.ts`](../../../externel_projects/gemini-cli/packages/core/src/services/chatCompressionService.ts:101)
4. **Конвертер запросов**: [`externel_projects/gemini-cli/packages/core/src/code_assist/converter.ts`](../../../externel_projects/gemini-cli/packages/core/src/code_assist/converter.ts:119)
5. **Клиент**: [`externel_projects/gemini-cli/packages/core/src/core/client.ts`](../../../externel_projects/gemini-cli/packages/core/src/core/client.ts:927)
6. **Тестовые данные**: [`externel_projects/gemini-cli/packages/core/src/services/test-data/resolved-aliases.golden.json`](../../../externel_projects/gemini-cli/packages/core/src/services/test-data/resolved-aliases.golden.json:1)

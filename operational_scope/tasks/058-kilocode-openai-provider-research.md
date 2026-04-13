# Исследование `KiloCode`: как проект реализует общение с OpenAI Provider

## Контекст

Для следующего архитектурного шага в `llm_agent_platform` нужно понять, как open source проект `KiloCode` реализует интеграцию с OpenAI Provider и где у него живут provider-specific model capabilities, request parameters и model-specific options.

Это исследование нужно как evidence input для будущего дизайна:

- `provider-specific model capability registry`;
- `key-scoped request policy overrides`;
- admin/UI выбора допустимых model-specific параметров, начиная с `reasoning level`.

Исходный код reference проекта находится в [`externel_projects/kilocode`](../../externel_projects/kilocode).

## Goal

Найти и проанализировать, как `KiloCode` реализует общение с OpenAI Provider, и подготовить evidence-based выводы, которые можно использовать в архитектурном дизайне `llm_agent_platform`.

## Scope

В scope:

- code reading в [`externel_projects/kilocode`](../../externel_projects/kilocode);
- поиск entry points, adapters, transport layer, model registry и parameter handling для OpenAI Provider;
- поиск evidence о том, как проект определяет model-specific capabilities и request parameters;
- анализ того, где и как задаются допустимые значения reasoning-related или других special params;
- фиксация архитектурных выводов и mapping на потребности `llm_agent_platform`.

Не входит в scope:

- production implementation в `llm_agent_platform`;
- изменение reference repo `KiloCode`;
- полный обзор всех providers `KiloCode`, если они не нужны для понимания OpenAI integration path.

## Research questions

1. Где в `KiloCode` находится основной entry point для общения с OpenAI Provider?
2. Какие модули отвечают за:
   - provider selection;
   - model selection;
   - transport/client initialization;
   - request payload construction;
   - response normalization?
3. Есть ли у `KiloCode` provider-specific registry моделей или capabilities, и где он materialized?
4. Есть ли у `KiloCode` model-specific metadata для reasoning или других special params?
5. Если metadata нет в явном виде, где в коде зашиты supported params и allowed values?
6. Есть ли evidence, что project умеет читать допустимые значения параметров из JSON/schema/config, а не только из hardcoded logic?
7. Как `KiloCode` связывает выбранную модель с набором допустимых request parameters?
8. Какой shape данных или pattern из `KiloCode` можно адаптировать под `provider-specific capability registry` в `llm_agent_platform`?
9. Какие части подхода `KiloCode` плохо совместимы с нашим provider-centric каноном?

## Required deliverables

Нужен evidence-based report со следующими частями:

1. `Summary`
2. `OpenAI Integration Entry Points`
3. `Provider and Model Resolution`
4. `Model Capabilities and Parameters`
5. `Reasoning or Special Parameter Evidence`
6. `Relevant Files and Code Paths`
7. `Mapping to llm_agent_platform`
8. `Trade-offs and Limitations`
9. `Unknowns / White Spots`
10. `Recommendation for our platform`

## Output requirements

- Для каждого важного вывода указывать конкретные файлы и code paths.
- Явно отделять факты из кода от assumptions.
- Если точный API OpenAI Provider неочевиден, нужно показать, что именно удалось подтвердить, а что осталось unknown.
- Если reasoning-related support найден только косвенно, это нужно честно зафиксировать.

## Context files

- [`docs/vision.md`](../../docs/vision.md)
- [`docs/architecture/openai-chat-completions-pipeline.md`](../../docs/architecture/openai-chat-completions-pipeline.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`services/backend/llm_agent_platform/api/openai/pipeline.py`](../../services/backend/llm_agent_platform/api/openai/pipeline.py)
- [`services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py`](../../services/backend/llm_agent_platform/api/openai/providers/openai_chatgpt.py)
- [`services/backend/llm_agent_platform/services/openai_chatgpt_api_keys.py`](../../services/backend/llm_agent_platform/services/openai_chatgpt_api_keys.py)
- [`externel_projects/kilocode`](../../externel_projects/kilocode)

## Research method

- Исследован runtime path в `packages/opencode/src/provider/`, `packages/opencode/src/session/`, `packages/opencode/src/plugin/` и TUI state/UI, которые materialize provider/model selection и request option handling.
- Отдельно проверены `ModelsDev`, config schema и plugin-based auth path, чтобы отделить data-driven metadata от hardcoded request logic.
- Выводы ниже основаны только на code reading reference repo `externel_projects/kilocode`; внешняя документация не использовалась как primary evidence.

## Summary

- `KiloCode` не реализует OpenAI transport как отдельный first-class provider adapter внутри своего кода. Основной OpenAI runtime path собирается вокруг generic `Provider` namespace, а затем делегируется в bundled AI SDK provider `@ai-sdk/openai`; для OpenAI моделей `CUSTOM_LOADERS.openai` принудительно выбирает `sdk.responses(modelID)`, то есть Responses API path, а не chat/completions path. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:29`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:29), [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:91`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:91), [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:139`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:139), [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:1235`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:1235).
- Provider/model registry у `KiloCode` общий, не provider-centric в нашем смысле. Базовые модели приходят из `models.dev` и превращаются в `Provider.Model` с полями `capabilities`, `options`, `headers`, `variants`, `ai_sdk_provider`; затем config overlays и plugin/auth overlays дообогащают ту же структуру. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/models.ts:37`](../../externel_projects/kilocode/packages/opencode/src/provider/models.ts:37), [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:637`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:637), [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:815`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:815), [`externel_projects/kilocode/packages/opencode/src/config/config.ts:1082`](../../externel_projects/kilocode/packages/opencode/src/config/config.ts:1082).
- Model-specific capabilities для reasoning существуют, но allowed values reasoning levels в основном не читаются из JSON/schema. Они hardcoded в `ProviderTransform.variants()` и `ProviderTransform.options()` через ветвление по `model.api.npm`, `model.id`, `release_date` и provider-specific heuristics. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:381`](../../externel_projects/kilocode/packages/opencode/src/provider/transform.ts:381), [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:560`](../../externel_projects/kilocode/packages/opencode/src/provider/transform.ts:560), [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:755`](../../externel_projects/kilocode/packages/opencode/src/provider/transform.ts:755).
- Связка `selected model -> allowed request params` у `KiloCode` происходит не через явный registry contract, а через late-bound merge chain: `base options`/`small options` + `model.options` + `agent.options` + chosen `variant`, после чего итог превращается в providerOptions namespace для AI SDK. Evidence: [`externel_projects/kilocode/packages/opencode/src/session/llm.ts:105`](../../externel_projects/kilocode/packages/opencode/src/session/llm.ts:105), [`externel_projects/kilocode/packages/opencode/src/session/llm.ts:114`](../../externel_projects/kilocode/packages/opencode/src/session/llm.ts:114), [`externel_projects/kilocode/packages/opencode/src/session/llm.ts:220`](../../externel_projects/kilocode/packages/opencode/src/session/llm.ts:220), [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:917`](../../externel_projects/kilocode/packages/opencode/src/provider/transform.ts:917).
- Для OpenAI OAuth существует special-case path через `CodexAuthPlugin`: plugin урезает список OpenAI моделей до Codex-совместимых, подменяет `fetch`, переписывает URL на `https://chatgpt.com/backend-api/codex/responses`, проставляет `Authorization`/`ChatGPT-Account-Id`, но при этом сохраняет provider id `openai` и npm `@ai-sdk/openai`. Это важный признак, что provider identity и upstream transport/runtime endpoint в `KiloCode` могут расходиться. Evidence: [`externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:358`](../../externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:358), [`externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:366`](../../externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:366), [`externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:423`](../../externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:423), [`externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:488`](../../externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:488).

## OpenAI Integration Entry Points

### Confirmed facts

- Bundled provider factory map регистрирует `@ai-sdk/openai` через `createOpenAI`; это low-level SDK constructor для OpenAI transport. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:91`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:91).
- `CUSTOM_LOADERS.openai.getModel()` всегда возвращает `sdk.responses(modelID)`. Значит обычный OpenAI provider в `KiloCode` ориентирован на Responses API surface. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:139`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:139).
- Session runtime берет `Provider.getLanguage(model)` и передает результат в `streamText()`. Сам runtime поток для всех providers общий; OpenAI-specific branching происходит до вызова `streamText()` через provider/model/options preparation. Evidence: [`externel_projects/kilocode/packages/opencode/src/session/llm.ts:66`](../../externel_projects/kilocode/packages/opencode/src/session/llm.ts:66), [`externel_projects/kilocode/packages/opencode/src/session/llm.ts:190`](../../externel_projects/kilocode/packages/opencode/src/session/llm.ts:190).
- Для OpenAI OAuth/Codex plugin auth loader подменяет request transport собственным `fetch`, удаляет dummy API key, refresh-ит access token, подставляет bearer token и переписывает target URL на Codex responses endpoint. Evidence: [`externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:423`](../../externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:423), [`externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:439`](../../externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:439), [`externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:488`](../../externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:488).

### Interpretation

- Главный OpenAI entry point в архитектурном смысле не один файл, а chain `Provider.getLanguage()` -> `getSDK()` -> `CUSTOM_LOADERS.openai.getModel()` -> `LLM.stream()`.
- У `KiloCode` нет собственного OpenAI response normalizer для обычного OpenAI provider; normalizer в основном делегирован AI SDK. Собственная логика ограничена message/providerOptions preprocessing и custom fetch wrapper.

## Provider and Model Resolution

### Confirmed facts

- `ModelsDev.get()` загружает глобальную provider/model database из cache/snapshot/`models.dev`, после чего `Provider.state()` строит in-memory registry providers. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/models.ts:119`](../../externel_projects/kilocode/packages/opencode/src/provider/models.ts:119), [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:815`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:815).
- `fromModelsDevModel()` materialize-ит generic `Provider.Model`, где provider identity и transport hints лежат рядом: `providerID`, `api.id`, `api.url`, `api.npm`, `capabilities`, `options`, `headers`, `variants`, `ai_sdk_provider`. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:730`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:730).
- Config schema разрешает provider-level and model-level overrides, включая custom `models`, `options`, `whitelist`, `blacklist` и `variants`. Evidence: [`externel_projects/kilocode/packages/opencode/src/config/config.ts:1082`](../../externel_projects/kilocode/packages/opencode/src/config/config.ts:1082).
- Во время `Provider.state()` registry собирается из models database, config providers, env keys, stored auth и plugin auth loaders, затем фильтруется по enabled/disabled providers и whitelist/blacklist моделей. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:817`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:817), [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:868`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:868), [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:958`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:958), [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:1028`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:1028), [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:1053`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:1053).
- `getSDK()` resolves runtime client from `model.api.npm`; bundled providers are instantiated directly, dynamic providers may be installed at runtime. `getLanguage()` then either calls model-specific loader or generic `sdk.languageModel(model.api.id)`. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:1178`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:1178), [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:1235`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:1235).

### Interpretation

- Provider selection у `KiloCode` фактически registry-driven, но registry не закрепляет provider contract boundary так жестко, как наш provider-centric canon. Один и тот же `providerID` может использовать plugin-patched transport behavior, а конкретный HTTP surface определяется поздно через `api.npm`, `api.url`, auth loader и custom `fetch`.

## Model Capabilities and Parameters

### Confirmed facts

- Capabilities приходят в основном из `ModelsDev.Model`: `reasoning`, `temperature`, `tool_call`, `modalities`, `interleaved`, `options`, `headers`, `variants`, `ai_sdk_provider`. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/models.ts:41`](../../externel_projects/kilocode/packages/opencode/src/provider/models.ts:41).
- Эти данные переносятся в internal `Provider.Model`; для всех providers, кроме `kilo`, исходные `model.variants` не сохраняются напрямую, после чего `ProviderTransform.variants()` повторно вычисляет variants из code logic. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:790`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:790), [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:799`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:799).
- В config schema можно data-driven override-ить `ModelsDev.Model.partial()`, включая `options`, `headers` и дополнительные `variants`. Evidence: [`externel_projects/kilocode/packages/opencode/src/config/config.ts:1086`](../../externel_projects/kilocode/packages/opencode/src/config/config.ts:1086).
- Runtime options для конкретного запроса строятся в `LLM.stream()`: сначала `ProviderTransform.options()` или `smallOptions()`, затем merge с `input.model.options`, `input.agent.options` и выбранным `variant`. Evidence: [`externel_projects/kilocode/packages/opencode/src/session/llm.ts:105`](../../externel_projects/kilocode/packages/opencode/src/session/llm.ts:105), [`externel_projects/kilocode/packages/opencode/src/session/llm.ts:114`](../../externel_projects/kilocode/packages/opencode/src/session/llm.ts:114).
- Перед вызовом AI SDK итоговые top-level options переносятся в provider namespace через `ProviderTransform.providerOptions()`: для `@ai-sdk/openai` ключ будет `openai`, для gateway - derived upstream slug, для `kilo-gateway` - отдельный mapper `kiloProviderOptions()`. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:917`](../../externel_projects/kilocode/packages/opencode/src/provider/transform.ts:917), [`externel_projects/kilocode/packages/opencode/src/kilocode/provider-options.ts:6`](../../externel_projects/kilocode/packages/opencode/src/kilocode/provider-options.ts:6).

### Interpretation

- `KiloCode` имеет частично data-driven capability layer, но request-parameter policy layer остается code-driven. Это две разные плоскости, не оформленные как отдельные контракты.

## Reasoning or Special Parameter Evidence

### Confirmed facts

- `ProviderTransform.variants()` hardcode-ит reasoning variants по `model.api.npm` и `model.id`; для `@ai-sdk/openai` variants строятся как map `effort -> { reasoningEffort, reasoningSummary, include }`, причем доступные efforts зависят от `gpt-5`, `codex`, `release_date` и исключения `gpt-5-pro`. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:560`](../../externel_projects/kilocode/packages/opencode/src/provider/transform.ts:560).
- Для generic OpenAI-compatible providers reasoning efforts зашиты как `low|medium|high`, без отдельного per-model registry. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:530`](../../externel_projects/kilocode/packages/opencode/src/provider/transform.ts:530).
- `ProviderTransform.options()` задает default special params для GPT-5 family: `reasoningEffort = medium`, `reasoningSummary = auto`, а для части non-chat GPT-5.x еще и `textVerbosity = low`. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:834`](../../externel_projects/kilocode/packages/opencode/src/provider/transform.ts:834).
- Для OpenAI requests по умолчанию также задаются `store = false` и `promptCacheKey = sessionID`. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:762`](../../externel_projects/kilocode/packages/opencode/src/provider/transform.ts:762), [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:795`](../../externel_projects/kilocode/packages/opencode/src/provider/transform.ts:795).
- Runtime fetch wrapper для `@ai-sdk/openai` модифицирует POST body, удаляя `id` у items в `body.input`, кроме Azure + `store=true` special case. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:1153`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:1153).
- Для OpenAI OAuth/Codex path plugin ограничивает доступный model set и добавляет synthetic model `gpt-5.3-codex`, после чего для него тоже вычисляются variants через тот же hardcoded `ProviderTransform.variants()`. Evidence: [`externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:366`](../../externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:366), [`externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:382`](../../externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:382), [`externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:410`](../../externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:410).

### Direct answer to research questions 4-7

- Явное model-specific metadata есть только частично: `reasoning: boolean`, `interleaved`, `options`, `headers`, `variants`, `ai_sdk_provider` присутствуют в model data shape, но allowed reasoning values не приходят как canonical schema field. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/models.ts:41`](../../externel_projects/kilocode/packages/opencode/src/provider/models.ts:41).
- Supported params и allowed values для reasoning, verbosity и cache behavior для OpenAI в основном зашиты в `ProviderTransform.variants()` и `ProviderTransform.options()`, а не описаны external JSON schema. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:381`](../../externel_projects/kilocode/packages/opencode/src/provider/transform.ts:381), [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:755`](../../externel_projects/kilocode/packages/opencode/src/provider/transform.ts:755).
- Evidence data-driven loading есть только для coarse metadata/config overrides: `ModelsDev.get()` читает JSON models catalog, config schema читает provider/model overrides, а UI читает `info.variants` для переключения. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/models.ts:119`](../../externel_projects/kilocode/packages/opencode/src/provider/models.ts:119), [`externel_projects/kilocode/packages/opencode/src/config/config.ts:1082`](../../externel_projects/kilocode/packages/opencode/src/config/config.ts:1082), [`externel_projects/kilocode/packages/opencode/src/cli/cmd/tui/context/local.tsx:353`](../../externel_projects/kilocode/packages/opencode/src/cli/cmd/tui/context/local.tsx:353).
- Связка model -> allowed params materialize-ится через runtime merge и then-through variant selection, а не через отдельную validation contract. Пользователь/agent выбирает variant, UI показывает список `Object.keys(info.variants)`, а `LLM.stream()` просто merge-ит выбранный variant в request options. Evidence: [`externel_projects/kilocode/packages/opencode/src/cli/cmd/tui/context/local.tsx:353`](../../externel_projects/kilocode/packages/opencode/src/cli/cmd/tui/context/local.tsx:353), [`externel_projects/kilocode/packages/opencode/src/session/llm.ts:105`](../../externel_projects/kilocode/packages/opencode/src/session/llm.ts:105).

## Relevant Files and Code Paths

- Registry and client bootstrapping:
  - [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts)
  - [`externel_projects/kilocode/packages/opencode/src/provider/models.ts`](../../externel_projects/kilocode/packages/opencode/src/provider/models.ts)
  - [`externel_projects/kilocode/packages/opencode/src/config/config.ts`](../../externel_projects/kilocode/packages/opencode/src/config/config.ts)
- Request option and variant derivation:
  - [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts`](../../externel_projects/kilocode/packages/opencode/src/provider/transform.ts)
  - [`externel_projects/kilocode/packages/opencode/src/session/llm.ts`](../../externel_projects/kilocode/packages/opencode/src/session/llm.ts)
- OpenAI-specific auth/transport special case:
  - [`externel_projects/kilocode/packages/opencode/src/plugin/codex.ts`](../../externel_projects/kilocode/packages/opencode/src/plugin/codex.ts)
- UI consumption of model variants:
  - [`externel_projects/kilocode/packages/opencode/src/cli/cmd/tui/context/local.tsx`](../../externel_projects/kilocode/packages/opencode/src/cli/cmd/tui/context/local.tsx)

## Mapping to llm_agent_platform

### Reusable patterns

- Полезно reuse-ить разделение на coarse capability metadata (`reasoning`, modalities, tool support) и runtime option overlays (`options`, `headers`, `variants`). У `KiloCode` это уже видно в `Provider.Model`, хотя и не доведено до строгого контракта. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/provider.ts:637`](../../externel_projects/kilocode/packages/opencode/src/provider/provider.ts:637).
- Полезен pattern `variant` как UI/admin-friendly label для группировки допустимых parameter bundles. Для нашей платформы его можно превратить в explicit registry entity типа `parameter_profile` или `reasoning_level_profile`. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:381`](../../externel_projects/kilocode/packages/opencode/src/provider/transform.ts:381), [`externel_projects/kilocode/packages/opencode/src/cli/cmd/tui/context/local.tsx:353`](../../externel_projects/kilocode/packages/opencode/src/cli/cmd/tui/context/local.tsx:353).
- Полезен merge chain `provider defaults -> model metadata -> policy override -> user-selected variant`, но у нас он должен быть закреплен contract-first и validated before provider dispatch.

### Poor fit with our provider-centric canon

- `providerID` у `KiloCode` не гарантирует уникальный runtime contract: OpenAI OAuth/Codex path использует тот же `providerID = openai`, но другой endpoint/auth semantics. Для `llm_agent_platform` это плохой fit, потому что у нас provider - основная runtime сущность, а transport/auth semantics должны быть provider-owned, а не plugin-patched. Evidence: [`externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:361`](../../externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:361), [`externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:488`](../../externel_projects/kilocode/packages/opencode/src/plugin/codex.ts:488).
- Allowed values reasoning levels вычисляются ad hoc по строковым эвристикам (`id.includes`, `release_date` comparisons). Для нашей платформы это слишком неявно и плохо пригодно для admin surface, persisted policy и auditability. Evidence: [`externel_projects/kilocode/packages/opencode/src/provider/transform.ts:563`](../../externel_projects/kilocode/packages/opencode/src/provider/transform.ts:563).
- Validation граница слабая: config и models catalog могут supply metadata, но итоговые request params формируются поздно и не валидируются against explicit provider/model schema before dispatch.

## Trade-offs and Limitations

- Сильная сторона подхода `KiloCode`: быстро добавлять provider/model support через общий `Provider.Model` shape и небольшой объём glue-кода.
- Цена этого подхода: semantics reasoning/support spread across `models.dev`, config, plugin loaders и hardcoded transform heuristics, поэтому ответ на вопрос "какие значения параметра допустимы для этой модели?" нельзя получить из одного канонического registry source.
- OpenAI integration сильно опирается на AI SDK abstraction. Это уменьшает количество собственного кода, но скрывает transport/payload details за внешней библиотекой; внутри `KiloCode` подтверждается только pre-processing и option mapping слой.
- UI variants в `KiloCode` больше похожи на convenience toggle, чем на enforceable policy contract. Это хороший UX pattern, но слабая основа для platform-grade admin governance.

## Unknowns / White Spots

- Не подтвержден exact HTTP payload shape обычного OpenAI Responses request внутри `@ai-sdk/openai`, потому что этот код лежит за пределами исследованного reference repo. В `KiloCode` подтвержден только слой до вызова SDK и fetch wrapper вокруг него.
- Не найден явный schema validator, который бы до отправки проверял, что выбранный variant действительно допустим для конкретной OpenAI модели; судя по коду, эта гарантия опирается на то, что variants генерируются самим кодом и не проходят отдельный contract validation pass.
- Не найден отдельный canonical file, где OpenAI model capability registry жил бы как самостоятельный artifact; registry размазан между `models.dev` JSON data и transform logic.

## Recommendation for our platform

1. Не копировать `KiloCode`-подход буквально. Для `llm_agent_platform` provider identity, auth semantics, transport surface и capability registry должны оставаться одной provider-owned contract boundary.
2. Заимствовать только shape-идею: хранить coarse model metadata отдельно от request-parameter profiles, но materialize это в explicit provider-scoped registry, а не в hardcoded `if/else` по `model.id`.
3. Ввести canonical сущности уровня `provider_model_capabilities` и `provider_model_parameter_profiles`, где `reasoning_level`/`verbosity`/special params имеют allowed values, source-of-truth provenance и admin/UI labels.
4. Развести `default request policy`, `key-scoped overrides` и `user-selected profile` как три отдельных слоя merge, каждый со своей traceability и validation.
5. Если нужен UX-паттерн как в `KiloCode` variants, использовать его только как thin presentation layer поверх registry-backed profiles, а не как primary source of truth.

## Final status

- Current State: completed.
- Verification: targeted code reading completed for `externel_projects/kilocode` OpenAI integration path.
- Blockers: none.

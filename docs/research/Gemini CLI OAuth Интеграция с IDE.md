# **ПРОЕКТИРОВАНИЕ И РЕАЛИЗАЦИЯ ШЛЮЗА DOCKER ДЛЯ МОДЕЛЕЙ GEMINI (VERTEX AI) С OPENAI-СОВМЕСТИМЫМ ИНТЕРФЕЙСОМ И OAUTH-АВТОРИЗАЦИЕЙ**

## **1\. Введение и архитектурный контекст**

В современной экосистеме разработки программного обеспечения с использованием искусственного интеллекта (AI-assisted development) наблюдается фундаментальный разрыв между стандартами интерфейсов и корпоративными требованиями к инфраструктуре. С одной стороны, де\-факто стандартом взаимодействия с большими языковыми моделями (LLM) стал API, разработанный компанией OpenAI. Этот стандарт, основанный на REST-интерфейсах /v1/chat/completions, жестко "зашит" в архитектуру большинства современных инструментов разработки, таких как Cursor, Kilo Code, Cline и других агентов кодирования.1 Эти инструменты ожидают определенную структуру JSON-полей, специфический формат потоковой передачи данных (Server-Sent Events — SSE) и механизмы обработки ошибок, свойственные экосистеме OpenAI.  
С другой стороны, корпоративный сектор и разработчики, ориентированные на облачную экосистему Google, отдают предпочтение моделям семейства Gemini (Gemini 1.5 Pro, Flash), развернутым через платформу Vertex AI. Vertex AI предлагает преимущества в виде интеграции с IAM (Identity and Access Management), соответствия требованиям безопасности (SOC2, HIPAA), отсутствия использования данных для обучения моделей и высокой пропускной способности. Однако нативный интерфейс Vertex AI радикально отличается от стандарта OpenAI: он использует gRPC или REST API с отличной схемой данных (generateContent вместо chat/completions), другой механизм аутентификации (OAuth 2.0 Bearer tokens вместо статических ключей sk-...) и иную логику обработки ролей (например, строгое разделение системных инструкций).3  
Данный отчет представляет собой исчерпывающее техническое руководство и архитектурное обоснование решения, призванного устранить этот разрыв. Мы рассматриваем проектирование промежуточного слоя (proxy gateway), развернутого в Docker-контейнере, который выполняет трансляцию запросов "на лету". Ключевой особенностью предлагаемой архитектуры является отказ от статических сервисных аккаунтов (JSON-ключей), которые представляют угрозу безопасности, в пользу использования Application Default Credentials (ADC) через проброс сессии gcloud CLI внутрь контейнера. Это позволяет реализовать безопасную, короткоживущую авторизацию, соответствующую лучшим практикам DevSecOps.5  
В отчете также детально рассматривается интеграция этого шлюза с передовыми средами разработки Kilo Code v5 и Cursor, включая конфигурацию пользовательских режимов (custom modes), использование протокола контекста модели (MCP) и решение специфических проблем маршрутизации запросов в этих IDE.

## ---

**2\. Сравнительный анализ протоколов и необходимость адаптации**

Понимание глубины проблемы несовместимости требует детального анализа различий между ожидаемым клиентом форматом (OpenAI) и фактическим форматом провайдера (Vertex AI).

### **2.1 Структурные расхождения API**

Клиенты, такие как Kilo Code и Cursor, формируют HTTP POST запросы, содержащие массив messages. Каждый объект сообщения имеет поле role (system, user, assistant) и content.  
В противовес этому, Vertex AI API оперирует понятием contents, состоящим из parts. Системные инструкции часто выносятся в отдельное поле system\_instruction на верхнем уровне объекта запроса, а не включаются в общий массив сообщений. Более того, Vertex AI имеет строгие валидаторы очередности сообщений (например, чередование user/model), которые могут не соблюдаться клиентами OpenAI, допускающими более гибкую структуру.3  
Ниже представлена сравнительная таблица ключевых параметров двух интерфейсов:

| Характеристика | Спецификация OpenAI (Клиент) | Спецификация Vertex AI (Провайдер) | Задача адаптера (LiteLLM) |
| :---- | :---- | :---- | :---- |
| **Endpoint** | /v1/chat/completions | .../publishers/google/models/{MODEL}:streamGenerateContent | Маршрутизация URL и подстановка Project ID/Location |
| **Аутентификация** | Статический токен Authorization: Bearer sk-... | OAuth 2.0 Access Token (короткоживущий) | Генерация токена из ADC и его ротация |
| **Структура тела** | messages: \[{role, content}\] | contents: \[{role, parts: \[{text}\]}\] | Ремаппинг JSON-структуры, извлечение системного промпта |
| **Параметры** | max\_tokens, presence\_penalty | maxOutputTokens, параметры пенализации часто отсутствуют | Трансляция имен параметров, отброс неподдерживаемых (drop\_params: true) 8 |
| **Потоки (Streaming)** | SSE с дельтами choices.delta.content | SSE с полными чанками или gRPC stream | Преобразование чанков Vertex в формат OpenAI SSE |

### **2.2 Роль промежуточного слоя (Middleware)**

Для решения задачи адаптации используется паттерн "Adapter" или "Proxy". В качестве ядра этого слоя выбрана библиотека **LiteLLM**. Она предоставляет унифицированный интерфейс ввода-вывода, совместимый с OpenAI, и имеет встроенные драйверы для взаимодействия с Vertex AI. LiteLLM берет на себя тяжелую работу по валидации схем, управлению токенизацией и, что критически важно для данного отчета, взаимодействию с механизмами аутентификации Google Cloud.9

## ---

**3\. Архитектура безопасности и управления идентификацией (IAM)**

Центральным требованием к разрабатываемой системе является использование gcloud CLI / ADC для авторизации. Это требование диктуется необходимостью исключить хранение долгоживущих секретов (Service Account Keys) на локальных машинах разработчиков.

### **3.1 Механизм Application Default Credentials (ADC)**

ADC — это стратегия, используемая библиотеками Google Cloud для автоматического поиска учетных данных в среде выполнения. Порядок поиска обычно следующий:

1. Переменная окружения GOOGLE\_APPLICATION\_CREDENTIALS, указывающая на JSON-файл.  
2. Учетные данные, предоставленные через gcloud auth application-default login.  
3. Сервисный аккаунт, привязанный к ресурсу (если запущено в Compute Engine, Cloud Run и т.д.).11

В контексте локальной разработки Docker-контейнер представляет собой изолированную среду, которая по умолчанию не имеет доступа ни к конфигурации gcloud хост-машины, ни к её файловой системе. Следовательно, просто запустить контейнер недостаточно; необходимо явно "пробросить" состояние аутентификации внутрь.

### **3.2 Стратегия проброса учетных данных (Volume Mounting)**

Наиболее безопасным и эффективным методом является монтирование директории конфигурации gcloud хоста в контейнер. Файл application\_default\_credentials.json, создаваемый командой gcloud auth application-default login, содержит refresh token (токен обновления), который библиотека Google Auth внутри контейнера может использовать для получения access token (токена доступа).5  
Критические аспекты реализации:

* **Пути в файловой системе:** На хосте (Linux/macOS) файл обычно находится в \~/.config/gcloud. Внутри контейнера, если процесс запущен от пользователя root, библиотека ожидает найти его в /root/.config/gcloud или по пути, указанном в переменной окружения.  
* **Переносимость:** Использование переменных окружения для указания пути внутри контейнера делает решение устойчивым к изменениям базового образа.

### **3.3 Принцип наименьших привилегий (Least Privilege)**

Идентификатор, используемый для генерации ADC (обычно это персональный аккаунт разработчика), должен обладать минимально необходимым набором прав. Для инференса моделей Gemini через Vertex AI требуется роль:

* **Vertex AI User** (roles/aiplatform.user).13 Эта роль позволяет отправлять запросы на прогнозирование (prediction), но не позволяет создавать новые модели, управлять инфраструктурой или удалять ресурсы, что снижает риск в случае компрометации сессии.

## ---

**4\. Техническая реализация контейнеризированного решения**

В данном разделе представлена полная конфигурация Docker-окружения, объединяющая LiteLLM и механизм ADC.

### **4.1 Структура проекта**

Рекомендуется следующая структура файлов для обеспечения чистоты конфигурации и удобства сопровождения:  
gemini-gateway/  
├── docker-compose.yml \# Определение сервиса и томов  
├── litellm\_config.yaml \# Маршрутизация моделей и параметры прокси  
└──.env \# (Опционально) Локальные переменные окружения

### **4.2 Конфигурация прокси: litellm\_config.yaml**

Файл конфигурации определяет, как запросы клиентов (Kilo Code/Cursor) маппятся на реальные модели Vertex AI. Важно использовать префикс vertex\_ai/ для указания провайдера.14

YAML

model\_list:  
  \# Алиас для Gemini 1.5 Pro  
  \- model\_name: gemini-1.5-pro  
    litellm\_params:  
      model: vertex\_ai/gemini-1.5-pro  
      vertex\_project: "os.environ/GOOGLE\_CLOUD\_PROJECT"  
      vertex\_location: "os.environ/GOOGLE\_CLOUD\_LOCATION"  
      \# Опционально: настройки кэширования промптов  
        
  \# Алиас для Gemini 1.5 Flash (быстрая модель)  
  \- model\_name: gemini-1.5-flash  
    litellm\_params:  
      model: vertex\_ai/gemini-1.5-flash  
      vertex\_project: "os.environ/GOOGLE\_CLOUD\_PROJECT"  
      vertex\_location: "os.environ/GOOGLE\_CLOUD\_LOCATION"

  \# Алиас для совместимости с жестко заданными промптами "gpt-4"  
  \# Это позволяет инструментам, ожидающим gpt-4, прозрачно использовать Gemini  
  \- model\_name: gpt-4  
    litellm\_params:  
      model: vertex\_ai/gemini-1.5-pro  
      vertex\_project: "os.environ/GOOGLE\_CLOUD\_PROJECT"  
      vertex\_location: "os.environ/GOOGLE\_CLOUD\_LOCATION"

litellm\_settings:  
  drop\_params: true         \# Критично: удаляет параметры OpenAI, несовместимые с Vertex (напр. frequency\_penalty)   
  set\_verbose: false        \# Включить true для отладки потоков  
  json\_logs: true           \# Логирование в формате JSON для интеграции с системами мониторинга

### **4.3 Определение контейнера: docker-compose.yml**

Файл docker-compose.yml реализует логику монтирования томов и передачи переменных окружения. Особое внимание уделено кросс-платформенной совместимости путей к учетным данным.5

YAML

services:  
  gemini-proxy:  
    image: ghcr.io/berriai/litellm:main-latest  
    container\_name: gemini-enterprise-gateway  
    ports:  
      \- "4000:4000" \# Стандартный порт LiteLLM  
    volumes:  
      \# Монтирование конфигурации прокси  
      \-./litellm\_config.yaml:/app/config.yaml  
        
      \# КРИТИЧЕСКИ ВАЖНО: Монтирование учетных данных gcloud с хоста  
      \# Путь \~/.config/gcloud монтируется в /root/.config/gcloud контейнера.  
      \# Это работает для Linux и macOS. Для Windows путь может отличаться (%APPDATA%).  
      \- ${HOME}/.config/gcloud:/root/.config/gcloud  
      
    environment:  
      \# Указание пути к конфигу LiteLLM  
      \- LITELLM\_CONFIG\_PATH=/app/config.yaml  
        
      \# Переменные проекта Google Cloud (подставляются из.env или окружения хоста)  
      \- GOOGLE\_CLOUD\_PROJECT=${GOOGLE\_CLOUD\_PROJECT}  
      \- GOOGLE\_CLOUD\_LOCATION=${GOOGLE\_CLOUD\_LOCATION:-us-central1}  
        
      \# Явное указание пути к файлу credentials внутри контейнера  
      \# Это гарантирует, что библиотеки Google найдут файл, смонтированный выше  
      \- GOOGLE\_APPLICATION\_CREDENTIALS=/root/.config/gcloud/application\_default\_credentials.json  
        
      \# (Опционально) Мастер-ключ для защиты самого прокси.   
      \# Если не задан, прокси может быть открыт без авторизации (только для localhost).  
      \# Рекомендуется задать для Cursor, так как он требует непустой API key.  
      \- LITELLM\_MASTER\_KEY=sk-proxy-secret-key-12345  
        
    command: \[ "--config", "/app/config.yaml", "--port", "4000", "--detailed\_debug" \]  
    restart: unless-stopped

### **4.4 Процедура запуска и верификации**

Для корректного запуска системы необходимо выполнить следующую последовательность действий на хост-машине:

1. **Авторизация:** Выполните команду для генерации файла ADC.  
   Bash  
   gcloud auth application-default login

   Будет открыт браузер для входа в Google-аккаунт. После успеха файл application\_default\_credentials.json будет создан.  
2. **Настройка переменных окружения:**  
   Bash  
   export GOOGLE\_CLOUD\_PROJECT="your-project-id"  
   export GOOGLE\_CLOUD\_LOCATION="us-central1" \# Рекомендуемый регион 

3. **Запуск контейнера:**  
   Bash  
   docker-compose up \-d

4. **Проверка работоспособности (Health Check):**  
   Используйте curl для проверки эндпоинта моделей.  
   Bash  
   curl http://localhost:4000/v1/models \\  
     \-H "Authorization: Bearer sk-proxy-secret-key-12345"

## ---

**5\. Конфигурация инфраструктуры Google Cloud**

Успешная работа Docker-контейнера зависит от корректной настройки облачной части.

### **5.1 Активация API**

В целевом проекте Google Cloud необходимо активировать API платформы искусственного интеллекта. Без этого запросы от контейнера будут возвращать ошибки 403\.

Bash

gcloud services enable aiplatform.googleapis.com \--project "your-project-id"

### **5.2 Управление квотами и регионами**

Gemini 1.5 Pro имеет строгие ограничения квот (RPM \- requests per minute, TPM \- tokens per minute).

* **Выбор региона:** Для стабильности и доступа к последним версиям моделей рекомендуется использовать регион us-central1. Доступность моделей в европейских регионах может отставать.18  
* **Мониторинг:** При активном использовании Kilo Code, который может генерировать множество параллельных запросов для анализа контекста, квота RPM может быть быстро исчерпана. В этом случае LiteLLM будет возвращать ошибки 429 (Too Many Requests), которые IDE должны корректно обрабатывать (retry logic).

## ---

**6\. Глубокая интеграция с Kilo Code v5**

Kilo Code v5 представляет собой сложную среду с поддержкой пользовательских режимов (custom modes) и протокола MCP. Интеграция нашего шлюза требует настройки нескольких конфигурационных файлов.

### **6.1 Настройка провайдера API**

В интерфейсе Kilo Code v5 необходимо выбрать тип провайдера **"OpenAI Compatible"** (или "OpenAI", если используется подмена базового URL).

* **Base URL:** http://localhost:4000/v1 (Важно: указать суффикс /v1, так как Kilo добавляет к нему /chat/completions).19  
* **API Key:** Введите sk-proxy-secret-key-12345 (или то значение, которое указано в LITELLM\_MASTER\_KEY). Если ключ не задан в прокси, можно ввести любую строку, например sk-1234, так как клиент требует непустое поле.20  
* **Model ID:** gemini-1.5-pro (Должно совпадать с model\_name в litellm\_config.yaml).

### **6.2 Архитектура Custom Modes (Пользовательские режимы)**

Kilo Code v5 позволяет определять специализированные "персоны" агента через файлы конфигурации YAML. Это мощный инструмент для переключения между задачами (например, написание тестов vs архитектурное проектирование) с сохранением контекста и выбором инструментов.  
Конфигурация режимов может располагаться глобально или в корне проекта в файле .roomodes или .roo/custom\_modes.yaml.21 Использование YAML предпочтительнее JSON в новых версиях (v3.18+) из\-за поддержки многострочных строк и комментариев.  
**Пример конфигурации режима "Gemini Architect":**

YAML

customModes:  
  \- slug: gemini-architect  
    name: 🏛️ Gemini Architect  
    roleDefinition: \>  
      Ты — системный архитектор высокого уровня. Твоя цель — проектировать масштабируемые системы,  
      используя паттерны проектирования и принципы SOLID.  
      Ты работаешь на модели Gemini 1.5 Pro через Vertex AI.  
      Всегда создавай диаграммы Mermaid для визуализации решений.  
    groups:  
      \# Определение доступных групп инструментов \[22\]  
      \- read      \# Чтение файлов (анализ кодовой базы)  
      \- command   \# Выполнение команд терминала  
      \- mcp       \# Доступ к MCP серверам (критично для расширения возможностей)  
        
      \# Ограниченный доступ к редактированию (только документация)  
      \- \- edit  
        \- fileRegex: \\.md$  
          description: Разрешено редактировать только Markdown-файлы документации  
            
    customInstructions: \>  
      При анализе используй пошаговое рассуждение (Chain of Thought).  
      Не предлагай код реализации, пока не утверждена архитектура.

**Концепция "Sticky Models" (Липкие модели):** Kilo Code v5 реализует функцию "Sticky Models". Это означает, что если вы переключитесь в режим "Gemini Architect" и выберете модель gemini-1.5-pro (наш прокси), система запомнит этот выбор именно для этого режима. При переключении обратно в режим "Code" система может вернуть модель по умолчанию (например, Claude Sonnet, если она настроена). Это позволяет использовать дешевые модели для простых задач и мощные (Gemini Pro) для архитектурных.23

### **6.3 Интеграция с протоколом MCP (Model Context Protocol)**

MCP — это стандарт для подключения AI-моделей к внешним данным и инструментам. Kilo Code v5 выступает в роли MCP-клиента. Поскольку наш Docker-контейнер лишь транслирует текст, логика MCP выполняется на стороне Kilo Code (на хосте). Однако, прокси должен корректно передавать определения инструментов (tool definitions) от Kilo к Vertex AI и обратно.  
Gemini 1.5 Pro в Vertex AI отлично поддерживает вызов функций (Function Calling), что делает его идеальным бэкендом для MCP.  
**Настройка MCP серверов в Kilo Code:**  
Файл конфигурации обычно находится в:

* macOS: \~/Library/Application Support/Code/User/globalStorage/rooveterinaryinc.roo-code/settings/mcp\_settings.json  
* Linux: \~/.config/Code/User/globalStorage/rooveterinaryinc.roo-code/settings/mcp\_settings.json

Пример подключения MCP сервера для доступа к файловой системе (чтобы агент мог читать файлы за пределами воркспейса):

JSON

{  
  "mcpServers": {  
    "filesystem": {  
      "command": "npx",  
      "args": \["-y", "@modelcontextprotocol/server-filesystem", "/Users/dev/projects"\],  
      "alwaysAllow": \["read\_file", "list\_directory"\]   
    }  
  }  
}

*Важное примечание:* Параметр alwaysAllow позволяет агенту вызывать инструменты без подтверждения пользователя для каждой операции, что критично для автономных агентов.25

## ---

**7\. Интеграция с Cursor IDE: Стратегии и обходные пути**

Интеграция с Cursor имеет свои нюансы, связанные с тем, как IDE обрабатывает переопределение базовых URL.

### **7.1 Проблема "Override OpenAI Base URL"**

В Cursor существует известная особенность (или баг): при включении опции "Override OpenAI Base URL" в настройках, Cursor пытается маршрутизировать **все** запросы к моделям OpenAI через этот URL. Это может нарушить работу нативных функций Cursor (таких как Cursor Tab/Copilot++ или Composer), которые ожидают подключения к официальным серверам Cursor или OpenAI.26

### **7.2 Рекомендуемая конфигурация**

Чтобы минимизировать конфликты, рекомендуется следующий алгоритм:

1. **Добавление пользовательской модели (Custom Model):**  
   * Перейдите в Settings \-\> Models.  
   * В разделе "OpenAI API Key" введите ваш прокси-ключ (sk-proxy-secret-key-12345). Даже если аутентификация идет через Google, поле не должно быть пустым.28  
   * Включите тумблер **"Override OpenAI Base URL"** и введите http://localhost:4000/v1.  
   * **Важный шаг:** Нажмите кнопку **"Add Model"** и добавьте имя модели в точности так, как оно прописано в litellm\_config.yaml (например, gemini-1.5-pro).  
   * Убедитесь, что модель активирована (галочка стоит).  
2. **Обходной путь при конфликтах (Workaround):**  
   Если вы замечаете, что автодополнение кода (Tab) перестало работать или работает некорректно, используйте стратегию переключения:  
   * Включайте "Override OpenAI Base URL" **только** когда вы активно используете чат (Cmd+L) с моделью Gemini.  
   * Отключайте его для возврата к стандартному поведению Cursor Tab.  
   * *Альтернатива:* Некоторые пользователи сообщают об успехе при использовании отдельного проксирующего URL только для конкретных моделей, но текущий интерфейс Cursor применяет Override глобально к ключу OpenAI.29

### **7.3 Проверка потоковой передачи (Streaming)**

Cursor полагается на Server-Sent Events (SSE) для отображения текста по мере его генерации. Наш Docker-контейнер на базе LiteLLM автоматически преобразует потоковый ответ Vertex AI (который может приходить крупными чанками JSON) в стандартный формат data:..., ожидаемый Cursor. Если текст появляется рывками или только в конце генерации, проверьте параметр stream: true в логах LiteLLM и убедитесь, что между Cursor и Docker нет буферизирующих прокси (например, Nginx с включенным буфером).31

## ---

**8\. Эксплуатация, мониторинг и устранение неполадок**

Для обеспечения надежной работы шлюза в корпоративной среде необходимо настроить процессы мониторинга.

### **8.1 Логирование и аудит**

В файле litellm\_config.yaml рекомендуется установить general\_settings: { json\_logs: true }. Это заставит контейнер выводить логи в формате JSON, которые можно собирать через драйверы логирования Docker (например, в ELK стек или Google Cloud Logging). Это позволяет отслеживать:

* Реальное потребление токенов (Cost Tracking).  
* Латентность запросов к Vertex AI.  
* Ошибки валидации схем.

### **8.2 Матрица устранения неполадок**

| Симптом | Вероятная причина | Метод диагностики | Решение |
| :---- | :---- | :---- | :---- |
| **Ошибка 401 (Unauthorized)** | Контейнер не видит файл credentials. | docker exec \-it gemini-gateway ls \-la /root/.config/gcloud | Проверьте пути в volumes в docker-compose.yml. Убедитесь, что на хосте выполнен gcloud auth application-default login. |
| **Ошибка 403 (Forbidden)** | Отключен API или нет прав IAM. | Проверка логов контейнера на наличие сообщения от Google API. | Выполнить gcloud services enable aiplatform... и проверить роль Vertex AI User. |
| **Ошибка 429 (Too Many Requests)** | Исчерпана квота Vertex AI. | Просмотр Google Cloud Console \-\> Quotas. | Запросить увеличение квоты RPM для gemini-1.5-pro или настроить retries в клиенте. |
| **Зависание Cursor (Spinning)** | Проблема с буферизацией SSE или сетью. | Тест через curl \-N... | Убедиться, что порт 4000 доступен, и LiteLLM работает в режиме стриминга. |
| **"Model not found"** | Несовпадение имен моделей. | Сравнение litellm\_config.yaml и настроек IDE. | Имя в запросе клиента должно в точности совпадать с model\_name в конфиге прокси. |

### **8.3 Обновление токенов**

Токены доступа Google OAuth имеют ограниченный срок жизни (обычно 1 час). Библиотека Google Auth внутри контейнера автоматически использует Refresh Token из смонтированного файла application\_default\_credentials.json для обновления доступа. Однако, если вы отзовете доступы или перелогинитесь на хосте, файл на хосте изменится. Благодаря механизму bind mount в Docker, изменения файла на хосте мгновенно видны внутри контейнера, что обеспечивает непрерывность работы без перезапуска контейнера (в большинстве случаев, хотя некоторые библиотеки кэшируют файл при старте).

## ---

**9\. Заключение**

Представленная архитектура Docker-шлюза успешно решает проблему несовместимости интерфейсов между передовыми моделями Google Gemini и экосистемой инструментов разработки, ориентированной на OpenAI. Использование паттерна "Adapter" через LiteLLM в сочетании с безопасным пробросом ADC-авторизации позволяет корпоративным разработчикам использовать мощь Gemini 1.5 Pro в средах Kilo Code v5 и Cursor, не нарушая политик безопасности и не используя рискованные долгоживущие ключи.  
Реализация глубокой интеграции через custom modes в Kilo Code и настройка MCP открывает возможности для создания специализированных ИИ-агентов (архитекторов, тестировщиков), обладающих контекстом всего проекта и способных выполнять сложные многошаговые задачи. Несмотря на некоторые ограничения интеграции с Cursor (конфликты Override URL), предложенные обходные пути позволяют эффективно использовать данное решение в повседневной разработке.

#### **Источники**

1. bilal77511/custom-models-in-cursor-IDE \- GitHub, дата последнего обращения: января 31, 2026, [https://github.com/bilal77511/custom-models-in-cursor-IDE](https://github.com/bilal77511/custom-models-in-cursor-IDE)  
2. Kilo Code | AI/ML API Documentation, дата последнего обращения: января 31, 2026, [https://docs.aimlapi.com/integrations/kilo-code](https://docs.aimlapi.com/integrations/kilo-code)  
3. Using OpenAI libraries with Vertex AI \- Google Cloud Documentation, дата последнего обращения: января 31, 2026, [https://docs.cloud.google.com/vertex-ai/generative-ai/docs/migrate/openai/overview](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/migrate/openai/overview)  
4. OpenAI compatibility | Generative AI on Vertex AI, дата последнего обращения: января 31, 2026, [https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/openai](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/start/openai)  
5. Simple way to pass gcloud credentials to a docker container ... \- Reddit, дата последнего обращения: января 31, 2026, [https://www.reddit.com/r/googlecloud/comments/zhbfil/simple\_way\_to\_pass\_gcloud\_credentials\_to\_a\_docker/](https://www.reddit.com/r/googlecloud/comments/zhbfil/simple_way_to_pass_gcloud_credentials_to_a_docker/)  
6. Authentication on GCP with Docker: Application Default Credentials, дата последнего обращения: января 31, 2026, [https://medium.com/datamindedbe/authentication-on-gcp-application-default-credentials-477879e31cb5](https://medium.com/datamindedbe/authentication-on-gcp-application-default-credentials-477879e31cb5)  
7. litellm/docs/my-website/docs/providers/vertex.md at main \- GitHub, дата последнего обращения: января 31, 2026, [https://github.com/BerriAI/litellm/blob/main/docs/my-website/docs/providers/vertex.md](https://github.com/BerriAI/litellm/blob/main/docs/my-website/docs/providers/vertex.md)  
8. Build with your Favorite Models from the Vertex AI Model Garden ..., дата последнего обращения: января 31, 2026, [https://medium.com/google-cloud/build-with-your-favorite-models-from-the-vertex-ai-model-garden-with-litellm-0b140bf52a01](https://medium.com/google-cloud/build-with-your-favorite-models-from-the-vertex-ai-model-garden-with-litellm-0b140bf52a01)  
9. Gemini CLI \- LiteLLM, дата последнего обращения: января 31, 2026, [https://docs.litellm.ai/docs/tutorials/litellm\_gemini\_cli](https://docs.litellm.ai/docs/tutorials/litellm_gemini_cli)  
10. Quick Start \- LiteLLM Proxy CLI, дата последнего обращения: января 31, 2026, [https://docs.litellm.ai/docs/proxy/quick\_start](https://docs.litellm.ai/docs/proxy/quick_start)  
11. How Application Default Credentials works | Authentication, дата последнего обращения: января 31, 2026, [https://docs.cloud.google.com/docs/authentication/application-default-credentials](https://docs.cloud.google.com/docs/authentication/application-default-credentials)  
12. Introduction to the Vertex AI SDK for Python, дата последнего обращения: января 31, 2026, [https://docs.cloud.google.com/vertex-ai/docs/python-sdk/use-vertex-ai-python-sdk](https://docs.cloud.google.com/vertex-ai/docs/python-sdk/use-vertex-ai-python-sdk)  
13. LiteLLM Proxy for Google Cloud Generative AI \- GitHub, дата последнего обращения: января 31, 2026, [https://github.com/Cyclenerd/google-cloud-litellm-proxy](https://github.com/Cyclenerd/google-cloud-litellm-proxy)  
14. LiteLLM with OpenAI \- AG2, дата последнего обращения: января 31, 2026, [https://docs.ag2.ai/latest/docs/user-guide/models/litellm-proxy-server/openai/](https://docs.ag2.ai/latest/docs/user-guide/models/litellm-proxy-server/openai/)  
15. Blog \- LiteLLM, дата последнего обращения: января 31, 2026, [https://docs.litellm.ai/blog](https://docs.litellm.ai/blog)  
16. litellm/docs/my-website/docs/proxy/deploy.md at main \- GitHub, дата последнего обращения: января 31, 2026, [https://github.com/BerriAI/litellm/blob/main/docs/my-website/docs/proxy/deploy.md](https://github.com/BerriAI/litellm/blob/main/docs/my-website/docs/proxy/deploy.md)  
17. How do I put application\_default\_credentials.json from Google cloud ..., дата последнего обращения: января 31, 2026, [https://forums.docker.com/t/how-do-i-put-application-default-credentials-json-from-google-cloud-to-docker-compose/145195](https://forums.docker.com/t/how-do-i-put-application-default-credentials-json-from-google-cloud-to-docker-compose/145195)  
18. Using Gemini CLI Through LiteLLM Proxy \- DEV Community, дата последнего обращения: января 31, 2026, [https://dev.to/polar3130/using-gemini-cli-through-litellm-proxy-1627](https://dev.to/polar3130/using-gemini-cli-through-litellm-proxy-1627)  
19. Kilo Code Integration \- Adaptive, дата последнего обращения: января 31, 2026, [https://docs.llmadaptive.uk/developer-tools/kilo-code](https://docs.llmadaptive.uk/developer-tools/kilo-code)  
20. Using LiteLLM With Roo Code, дата последнего обращения: января 31, 2026, [https://docs.roocode.com/providers/litellm](https://docs.roocode.com/providers/litellm)  
21. Roo Code 3.18 Release Notes (2025-05-21), дата последнего обращения: января 31, 2026, [https://docs.roocode.com/update-notes/v3.18](https://docs.roocode.com/update-notes/v3.18)  
22. Customizing Modes | Roo Code Documentation, дата последнего обращения: января 31, 2026, [https://docs.roocode.com/features/custom-modes](https://docs.roocode.com/features/custom-modes)  
23. Roo Code: Comprehensive Knowledge Base \- Pratik's Git, дата последнего обращения: января 31, 2026, [https://git.pratiknarola.com/nikhilmundra/RooPrompts/src/commit/eb26f4c714063a546294eaa322071741500cdc95/roo.md](https://git.pratiknarola.com/nikhilmundra/RooPrompts/src/commit/eb26f4c714063a546294eaa322071741500cdc95/roo.md)  
24. Auto-Approving Actions | Roo Code Documentation, дата последнего обращения: января 31, 2026, [https://docs.roocode.com/features/auto-approving-actions](https://docs.roocode.com/features/auto-approving-actions)  
25. “Override OpenAI Base URL” breaks requests when pointing to ..., дата последнего обращения: января 31, 2026, [https://forum.cursor.com/t/override-openai-base-url-breaks-requests-when-pointing-to-openrouter/142520](https://forum.cursor.com/t/override-openai-base-url-breaks-requests-when-pointing-to-openrouter/142520)  
26. Fresh bugs with custom model \- Cursor \- Community Forum, дата последнего обращения: января 31, 2026, [https://forum.cursor.com/t/fresh-bugs-with-custom-model/148815](https://forum.cursor.com/t/fresh-bugs-with-custom-model/148815)  
27. How to Set Up Custom API Keys in Cursor: Complete Guide for 2025, дата последнего обращения: января 31, 2026, [https://www.cursor-ide.com/blog/cursor-custom-api-key-guide-2025](https://www.cursor-ide.com/blog/cursor-custom-api-key-guide-2025)  
28. Cursor Models Fail When Using BYOK OpenAI Key with Overridden ..., дата последнего обращения: января 31, 2026, [https://forum.cursor.com/t/cursor-models-fail-when-using-byok-openai-key-with-overridden-base-url-glm-4-7/147218](https://forum.cursor.com/t/cursor-models-fail-when-using-byok-openai-key-with-overridden-base-url-glm-4-7/147218)  
29. Custom base URLs for each custom model \- Feature Requests, дата последнего обращения: января 31, 2026, [https://forum.cursor.com/t/custom-base-urls-for-each-custom-model/147219](https://forum.cursor.com/t/custom-base-urls-for-each-custom-model/147219)  
30. /responses | liteLLM, дата последнего обращения: января 31, 2026, [https://docs.litellm.ai/docs/response\_api](https://docs.litellm.ai/docs/response_api)
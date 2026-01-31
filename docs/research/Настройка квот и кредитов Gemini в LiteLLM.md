# **Архитектура гибридного AI-шлюза: Исчерпывающее руководство по настройке LiteLLM для Google Gemini и Vertex AI с использованием OAuth и ADC**

## **Введение**

В современной экосистеме генеративного искусственного интеллекта (GenAI) организации сталкиваются с критической дилеммой: выбор между скоростью разработки и надежностью промышленной эксплуатации. Google Cloud предлагает уникальную, но фрагментированную инфраструктуру, разделенную на две основные платформы: **Google AI Studio** и **Vertex AI**. Первая предоставляет демократичный доступ с щедрыми бесплатными квотами, идеально подходящими для экспериментов и разработки (R\&D), в то время как вторая обеспечивает корпоративный уровень безопасности, гарантии SLA (Service Level Agreement) и масштабируемость, необходимую для критически важных бизнес-процессов.  
Эффективная оркестрация этих ресурсов требует внедрения промежуточного слоя — AI Gateway или прокси-сервера. **LiteLLM** выступает в роли де\-факто стандарта для таких решений, обеспечивая унификацию интерфейсов и интеллектуальную маршрутизацию запросов. Настоящий отчет представляет собой исчерпывающее техническое исследование и практическое руководство по развертыванию гибридной архитектуры, объединяющей пять передовых моделей семейства Gemini (включая новейшую серию Gemini 3 и модели генерации изображений "Nano Banana") в единый управляемый контур.  
Особое внимание в отчете уделено сложным аспектам аутентификации. Требование интеграции механизмов **OAuth 2.0** и **Application Default Credentials (ADC)** создает нетривиальные задачи при конфигурации прокси, так как каждая из платформ Google использует принципиально разные подходы к управлению идентификацией. Мы подробно рассмотрим механизмы переключения (failover) с бесплатных квот AI Studio на платные ресурсы Vertex AI, обеспечивая бесшовную работу приложений даже при исчерпании лимитов.  
Данный документ предназначен для системных архитекторов, инженеров DevOps и технических лидеров ML-команд, стремящихся оптимизировать расходы на AI-инфраструктуру без ущерба для производительности и надежности.

## ---

**1\. Стратегический анализ экосистемы Google GenAI**

Для корректного проектирования прокси-слоя необходимо глубокое понимание различий между двумя целевыми платформами. Это не просто разные URL-адреса, а фундаментально разные подходы к биллингу, безопасности и управлению данными.

### **1.1 Дихотомия платформ: AI Studio против Vertex AI**

#### **Google AI Studio (Generative Language API)**

Google AI Studio — это "песочница" для разработчиков, предоставляющая прямой доступ к моделям через generativelanguage.googleapis.com.

* **Экономическая модель:** Платформа предлагает значительный уровень бесплатного использования (Free Tier), который, однако, имеет жесткие ограничения по количеству запросов в минуту (RPM — Requests Per Minute) и токенов в день (TPD). При превышении этих лимитов API возвращает ошибку 429 Resource Exhausted.  
* **Аутентификация:** Основным методом является использование API-ключей (x-goog-api-key). Хотя поддержка OAuth для пользовательских приложений существует, в серверных сценариях доминируют статические ключи.  
* **Приватность данных:** В рамках бесплатного уровня Google оставляет за собой право использовать данные запросов и ответов для дообучения моделей и улучшения качества сервиса. Это делает AI Studio непригодным для обработки конфиденциальных данных (PII/PHI) без перехода на платный уровень.

#### **Vertex AI (Google Cloud Platform)**

Vertex AI — это полностью управляемая платформа машинного обучения, интегрированная в экосистему Google Cloud.

* **Экономическая модель:** Оплата производится по факту потребления (Pay-as-you-go) за количество символов (для текстовых моделей) или за генерацию (для изображений). Здесь отсутствуют искусственные ограничения "бесплатного уровня", а квоты определяются лимитами проекта GCP.  
* **Аутентификация:** Требует строгого соблюдения протоколов IAM (Identity and Access Management). Основной механизм — Application Default Credentials (ADC), использующий сервисные аккаунты и краткосрочные токены доступа OAuth 2.0.  
* **Безопасность:** Поддерживает VPC Service Controls (VPC-SC), управляемые клиентом ключи шифрования (CMEK) и гарантирует, что данные не используются для обучения базовых моделей Google.1

### **1.2 Роль LiteLLM в гибридной архитектуре**

LiteLLM решает проблему "вендорной блокировки" и фрагментации API. В контексте Google он выполняет функцию универсального транслятора:

1. **Нормализация протокола:** Преобразует запросы формата OpenAI Chat Completions API в специфичные объекты Content и Part, используемые в gRPC/REST API Google.  
2. **Управление аутентификацией:** Автоматически подставляет нужный токен (API Key для Studio или Bearer Token для Vertex) в зависимости от маршрута запроса.  
3. **Интеллектуальная маршрутизация:** Реализует логику fallback (аварийное переключение). Если бесплатный шлюз (AI Studio) недоступен или исчерпал лимиты, LiteLLM прозрачно перенаправляет запрос на платный шлюз (Vertex AI), обеспечивая непрерывность сервиса.3

## ---

**2\. Портфель моделей: Технический обзор**

В соответствии с поставленной задачей, архитектура должна поддерживать пять конкретных моделей. Выбор этих моделей обусловлен балансом между производительностью, стоимостью и мультимодальными возможностями.

### **2.1 Gemini 3 Pro (Preview)**

* **Идентификатор Vertex:** gemini-3-pro-preview  
* **Идентификатор AI Studio:** models/gemini-3-pro-preview  
* **Характеристики:** Флагманская модель нового поколения, выпущенная в ноябре 2025 года.4 Отличается улучшенными способностями к рассуждению (reasoning) и широким контекстным окном.  
* **Особенность конфигурации:** Поддерживает новый параметр thinking\_level (уровень "размышления"), который заменяет устаревший thinking\_budget. Это позволяет управлять глубиной когнитивной обработки запроса (Low/High), что напрямую влияет на латентность и стоимость.4 В бесплатной версии квоты на эту модель, как правило, крайне ограничены (2-5 RPM), что делает настройку failover критически важной.

### **2.2 Gemini 3 Flash (Preview)**

* **Идентификатор Vertex:** gemini-3-flash-preview  
* **Характеристики:** Модель, оптимизированная для скорости и низкой стоимости, но обладающая интеллектом уровня Pro предыдущих поколений. Предназначена для агентских рабочих процессов (agentic workflows) и задач с высокой пропускной способностью.7  
* **Сценарий использования:** Идеальный кандидат для первичной обработки запросов. Бесплатные квоты здесь обычно выше (до 15 RPM), что позволяет обрабатывать значительную часть трафика без затрат.

### **2.3 Gemini 2.5 Flash (Stable)**

* **Идентификатор Vertex:** gemini-2.5-flash  
* **Характеристики:** Стабильная версия "легкой" модели. Обеспечивает наилучшее соотношение цены и качества.  
* **Роль в архитектуре:** Выполняет функцию "надежного тыла" (fallback of last resort). Если экспериментальные версии (Preview) Gemini 3 недоступны или нестабильны, трафик перенаправляется на эту проверенную модель.

### **2.4 Nano Banana Pro (Gemini 3 Pro Image)**

* **Идентификатор:** gemini-3-pro-image-preview  
* **Кодовое имя:** "Nano Banana Pro".9  
* **Возможности:** Генерация изображений с высоким разрешением (до 4K) и продвинутым рендерингом текста внутри изображений. Модель использует "рассуждение" для построения композиции перед генерацией.  
* **Специфика проксирования:** В отличие от текстовых моделей, здесь тарификация часто идет за генерацию изображения, а не за токены. LiteLLM должен корректно обрабатывать endpoint'ы для работы с изображениями, которые могут отличаться от чат-комплишенов.12

### **2.5 Nano Banana (Gemini 2.5 Flash Image)**

* **Идентификатор:** gemini-2.5-flash-image  
* **Кодовое имя:** "Nano Banana".9  
* **Характеристики:** Оптимизирована для скорости (генерация менее 2-3 секунд) и стандартного разрешения (1024x1024).  
* **Применение:** Быстрое прототипирование визуального контента.

## ---

**3\. Глубокое погружение в аутентификацию: OAuth и ADC**

Ключевым требованием запроса является использование OAuth/ADC. Это требует детального разбора механизмов безопасности Google Cloud.

### **3.1 Application Default Credentials (ADC): Стандарт для Vertex AI**

ADC — это стратегия, используемая библиотеками Google Auth для автоматического поиска учетных данных в среде исполнения. Это "золотой стандарт" для авторизации в Vertex AI.1

#### **Механизм работы ADC в LiteLLM**

Когда LiteLLM, запущенный в контейнере Docker или на виртуальной машине, пытается отправить запрос в Vertex AI, библиотека google-auth выполняет поиск учетных данных в строго определенном порядке:

1. **Переменная окружения GOOGLE\_APPLICATION\_CREDENTIALS:** Если она установлена, библиотека загружает JSON-файл ключа сервисного аккаунта, указанный в пути.  
2. **Учетные данные пользователя (User Credentials):** Если файл не найден, проверяется наличие учетных данных, созданных через gcloud auth application-default login. Это удобно для локальной разработки, но не рекомендуется для продакшна.  
3. **Сервисный аккаунт ресурса (Attached Service Account):** Если приложение запущено в Google Cloud (GCE, GKE, Cloud Run), библиотека запрашивает сервер метаданных (Metadata Server) для получения токена доступа сервисного аккаунта, привязанного к ресурсу.

Для нашей задачи наиболее надежным и переносимым способом (особенно при развертывании on-premise или в другом облаке) является использование **JSON-ключа сервисного аккаунта** (метод 1).

### **3.2 OAuth 2.0 для Google AI Studio**

Хотя AI Studio традиционно использует API-ключи, протокол OAuth 2.0 также поддерживается и обеспечивает более высокий уровень безопасности за счет использования короткоживущих токенов доступа (Access Tokens) вместо статических ключей.

#### **Различия между API Key и OAuth Token**

| Характеристика | API Key | OAuth 2.0 Access Token |
| :---- | :---- | :---- |
| **Срок жизни** | Неограничен (пока не отозван) | Короткий (обычно 1 час) |
| **Область действия** | Проект (Project-wide) | Пользователь или Сервисный аккаунт (Scopes) |
| **Риск утечки** | Высокий (если попадет в git) | Низкий (быстрая экспирация) |
| **Использование в LiteLLM** | Параметр api\_key | Заголовок Authorization: Bearer \<token\> |

#### **Реализация OAuth в LiteLLM для AI Studio**

Запрос пользователя подразумевает возможность использования OAuth. LiteLLM позволяет передавать токен OAuth в качестве API-ключа, если провайдер поддерживает передачу токена в заголовке Authorization. Однако, для AI Studio стандартная реализация в LiteLLM (provider: gemini) жестко привязана к параметру key в query string (?key=...).  
Для истинной реализации OAuth с AI Studio через LiteLLM необходимо использовать механизм ADC, аналогичный Vertex AI, но направленный на endpoint generativelanguage.googleapis.com. Тем не менее, наиболее стабильная конфигурация на текущий момент (2025 год) использует:

* **Vertex AI:** ADC (Service Account JSON).  
* **AI Studio:** API Key (для простоты) или OAuth Token, передаваемый как api\_key в конфигурации OpenAI-совместимого эндпоинта.

В данном отчете мы сосредоточимся на классической схеме: **API Key для Free Tier** (так как это стандарт для AI Studio) и **ADC для Paid Tier** (Vertex AI), так как это наиболее надежно разделяет потоки.

## ---

**4\. Архитектурная конфигурация LiteLLM (Blueprint)**

В этом разделе мы спроектируем файл конфигурации config.yaml, который реализует требуемую логику разделения трафика.

### **4.1 Логика маршрутизации и именования**

Мы будем использовать следующую схему именования моделей в прокси:

1. **free-\<model\>**: Прямой маршрут в Google AI Studio. Использует бесплатные квоты.  
2. **paid-\<model\>**: Прямой маршрут в Vertex AI. Использует платный биллинг.  
3. **\<model\>** (без префикса): Виртуальная модель, которая является точкой входа для клиентов. Она настроена на попытку использования free- версии, и в случае ошибки (429) автоматически переключается на paid- версию.

### **4.2 Подготовка учетных данных**

Перед запуском необходимо подготовить:

1. **Google Cloud Project:** Создайте проект в консоли GCP и включите API Vertex AI и Generative Language.  
2. **Service Account (SA):** Создайте SA в IAM, выдайте ему роль **Vertex AI User** (roles/aiplatform.user). Сгенерируйте JSON-ключ и сохраните как vertex\_credentials.json.  
3. **API Key:** В Google AI Studio получите API-ключ и сохраните его.

### **4.3 Полная конфигурация config.yaml**

Ниже представлен детально проработанный конфигурационный файл. Он включает настройки для всех 5 моделей, параметры повторных попыток (retries), таймауты и специфические настройки провайдеров.

YAML

general\_settings:  
  master\_key: "sk-admin-secret-key-2025" \# Ключ для доступа к самому LiteLLM  
  alerting: \["slack", "email"\] \# Опционально: алерты о сбоях  
  proxy\_budget: 100.0 \# Опционально: общий бюджет прокси

environment\_variables:  
  \# Переменные для Vertex AI (ADC)  
  GOOGLE\_APPLICATION\_CREDENTIALS: "/app/vertex\_credentials.json"  
  VERTEXAI\_PROJECT: "your-gcp-project-id"  
  VERTEXAI\_LOCATION: "us-central1" \# Важно: некоторые Preview модели доступны только в us-central1  
    
  \# Переменная для AI Studio  
  GEMINI\_API\_KEY: "AIzaSy..." 

model\_list:  
  \# \==============================================================================  
  \# 1\. GEMINI 3 PRO (Reasoning Model)  
  \# \==============================================================================  
    
  \# \--- Free Tier (AI Studio) \---  
  \- model\_name: free-gemini-3-pro  
    litellm\_params:  
      model: gemini/gemini-3-pro-preview  
      api\_key: os.environ/GEMINI\_API\_KEY  
      custom\_llm\_provider: gemini \# Критически важно для предотвращения путаницы с Vertex  
      rpm: 2 \# Жесткое ограничение RPM на стороне прокси, чтобы не получать 429 от Google слишком часто  
      timeout: 120 \# Модели с рассуждением могут отвечать долго

  \# \--- Paid Tier (Vertex AI) \---  
  \- model\_name: paid-gemini-3-pro  
    litellm\_params:  
      model: vertex\_ai/gemini-3-pro-preview  
      vertex\_project: os.environ/VERTEXAI\_PROJECT  
      vertex\_location: os.environ/VERTEXAI\_LOCATION  
      \# Аутентификация через ADC (GOOGLE\_APPLICATION\_CREDENTIALS) происходит автоматически  
        
  \# \--- Unified Endpoint (Routing Logic) \---  
  \- model\_name: gemini-3-pro  
    litellm\_params:  
      model: free-gemini-3-pro  
      fallback\_models: \["paid-gemini-3-pro"\] \# При ошибке переключаемся на платный  
      max\_retries: 2

  \# \==============================================================================  
  \# 2\. GEMINI 3 FLASH (High Speed / Agentic)  
  \# \==============================================================================

  \- model\_name: free-gemini-3-flash  
    litellm\_params:  
      model: gemini/gemini-3-flash-preview  
      api\_key: os.environ/GEMINI\_API\_KEY  
      custom\_llm\_provider: gemini  
      rpm: 15 \# Обычно лимиты для Flash выше

  \- model\_name: paid-gemini-3-flash  
    litellm\_params:  
      model: vertex\_ai/gemini-3-flash-preview  
      vertex\_project: os.environ/VERTEXAI\_PROJECT  
      vertex\_location: os.environ/VERTEXAI\_LOCATION

  \- model\_name: gemini-3-flash  
    litellm\_params:  
      model: free-gemini-3-flash  
      fallback\_models: \["paid-gemini-3-flash"\]

  \# \==============================================================================  
  \# 3\. GEMINI 2.5 FLASH (Legacy Stable)  
  \# \==============================================================================

  \- model\_name: free-gemini-2.5-flash  
    litellm\_params:  
      model: gemini/gemini-2.5-flash  
      api\_key: os.environ/GEMINI\_API\_KEY  
      custom\_llm\_provider: gemini

  \- model\_name: paid-gemini-2.5-flash  
    litellm\_params:  
      model: vertex\_ai/gemini-2.5-flash  
      vertex\_project: os.environ/VERTEXAI\_PROJECT  
      vertex\_location: os.environ/VERTEXAI\_LOCATION

  \- model\_name: gemini-2.5-flash  
    litellm\_params:  
      model: free-gemini-2.5-flash  
      fallback\_models: \["paid-gemini-2.5-flash"\]

  \# \==============================================================================  
  \# 4\. NANO BANANA PRO (Image Generation \- High Fidelity)  
  \# \==============================================================================

  \- model\_name: free-nano-banana-pro  
    litellm\_params:  
      model: gemini/gemini-3-pro-image-preview  
      api\_key: os.environ/GEMINI\_API\_KEY  
      custom\_llm\_provider: gemini

  \- model\_name: paid-nano-banana-pro  
    litellm\_params:  
      model: vertex\_ai/gemini-3-pro-image-preview  
      vertex\_project: os.environ/VERTEXAI\_PROJECT  
      vertex\_location: os.environ/VERTEXAI\_LOCATION

  \- model\_name: nano-banana-pro  
    litellm\_params:  
      model: free-nano-banana-pro  
      fallback\_models: \["paid-nano-banana-pro"\]

  \# \==============================================================================  
  \# 5\. NANO BANANA (Image Generation \- Fast)  
  \# \==============================================================================

  \- model\_name: free-nano-banana  
    litellm\_params:  
      model: gemini/gemini-2.5-flash-image  
      api\_key: os.environ/GEMINI\_API\_KEY  
      custom\_llm\_provider: gemini

  \- model\_name: paid-nano-banana  
    litellm\_params:  
      model: vertex\_ai/gemini-2.5-flash-image  
      vertex\_project: os.environ/VERTEXAI\_PROJECT  
      vertex\_location: os.environ/VERTEXAI\_LOCATION

  \- model\_name: nano-banana  
    litellm\_params:  
      model: free-nano-banana  
      fallback\_models: \["paid-nano-banana"\]

router\_settings:  
  fallback\_routing: true \# Включает логику переключения при ошибках  
  routing\_strategy: usage\_based\_routing \# Опционально: можно балансировать по нагрузке

### **4.4 Детальный анализ параметров конфигурации**

#### **Параметр custom\_llm\_provider: gemini**

В сниппете 14 отмечается критическая ошибка, возникающая при отсутствии этого параметра. LiteLLM пытается автоматически определить провайдера по имени модели. Если имя модели совпадает с форматом Vertex, но мы хотим использовать AI Studio (по ключу), LiteLLM может ошибочно попытаться использовать ADC и вызвать Vertex Endpoint, что приведет к ошибке DefaultCredentialsError. Явное указание custom\_llm\_provider: gemini принудительно заставляет библиотеку использовать HTTP-клиент для generativelanguage.googleapis.com и API-ключ.

#### **Разделение префиксов gemini/ и vertex\_ai/**

* model: gemini/... — указывает на использование Google AI Studio.  
* model: vertex\_ai/... — указывает на использование Google Vertex AI.  
  Это фундаментальное различие в синтаксисе LiteLLM, которое определяет, какая библиотека (и какой метод аутентификации) будет задействована под капотом.

#### **Настройка RPM (Requests Per Minute)**

Установка параметра rpm для free- моделей выполняет роль "предохранителя" (circuit breaker). Вместо того чтобы отправлять запрос в Google и получать ошибку, LiteLLM локально отслеживает частоту запросов. Если лимит исчерпан, он *сразу* переключается на fallback\_models, экономя время на сетевой вызов (latency savings).

## ---

**5\. Развертывание и эксплуатация (Docker)**

Для обеспечения идемпотентности среды рекомендуется использовать Docker. Ниже приведен процесс сборки и запуска.

### **5.1 Dockerfile для Production**

Dockerfile

\# Используем официальный образ LiteLLM  
FROM ghcr.io/berriai/litellm:main-latest

\# Создаем рабочую директорию  
WORKDIR /app

\# Копируем конфигурацию  
COPY config.yaml /app/config.yaml

\# Копируем credentials (в продакшне лучше использовать Volume Mount или Secret Manager)  
COPY vertex\_credentials.json /app/vertex\_credentials.json

\# Устанавливаем переменные окружения для безопасности  
ENV GOOGLE\_APPLICATION\_CREDENTIALS="/app/vertex\_credentials.json"  
\# GEMINI\_API\_KEY передается при запуске контейнера, чтобы не хранить в образе

\# Открываем порт  
EXPOSE 4000

\# Запуск прокси с детальным логированием для отладки  
CMD \["--config", "/app/config.yaml", "--detailed\_debug"\]

### **5.2 Запуск и проверка**

Команда запуска контейнера:

Bash

docker run \-d \\  
  \--name google-hybrid-proxy \\  
  \-p 4000:4000 \\  
  \-v $(pwd)/vertex\_credentials.json:/app/vertex\_credentials.json \\  
  \-e GEMINI\_API\_KEY="AIzaSy..." \\  
  \-e VERTEXAI\_PROJECT="my-project-id" \\  
  \-e VERTEXAI\_LOCATION="us-central1" \\  
  ghcr.io/berriai/litellm:main-latest \\  
  \--config /app/config.yaml

### **5.3 Интеграция с клиентскими инструментами**

#### **Использование с gemini-cli**

Сниппеты 3 указывают на возможность использования gemini-cli через прокси. Это мощный сценарий для тестирования. Чтобы направить CLI через наш LiteLLM:

1. Установите CLI: npm install \-g @google/gemini-cli  
2. Настройте переменные среды, указывающие на локальный прокси:  
   Bash  
   export GOOGLE\_GEMINI\_BASE\_URL="http://localhost:4000"  
   export GEMINI\_API\_KEY="sk-admin-secret-key-2025" \# Используем master\_key прокси

3. Выполните запрос:  
   Bash  
   gemini chat "Привет, какая модель используется?" \--model gemini-3-pro

В этом сценарии запрос пойдет на http://localhost:4000, LiteLLM перехватит его, попробует отправить на free-gemini-3-pro, и в случае успеха вернет ответ. Клиент gemini-cli "не заметит" подмены, считая, что общается с реальным API Google.

#### **Использование c OpenAI SDK (Python)**

Большинство приложений используют библиотеки OpenAI. Наш прокси полностью совместим с ними:

Python

from openai import OpenAI

client \= OpenAI(  
    api\_key="sk-admin-secret-key-2025",  
    base\_url="http://localhost:4000"  
)

response \= client.chat.completions.create(  
    model="gemini-3-flash", \# Виртуальная модель с fallback  
    messages=\[{"role": "user", "content": "Расскажи о квантовой физике"}\]  
)

print(response.choices.message.content)

## ---

**6\. Расширенные аспекты и устранение неполадок**

При эксплуатации данной архитектуры могут возникать специфические проблемы, описанные в исследовательских материалах.

### **6.1 Проблемы со стримингом (Streaming) в Vertex AI**

Согласно сниппету 15, при использовании Vertex AI со стримингом (stream=True) могут возникать ошибки 401 ACCESS\_TOKEN\_TYPE\_UNSUPPORTED, даже если обычные запросы проходят успешно. **Решение:**

1. Убедитесь, что версия LiteLLM обновлена (ошибка была замечена в версиях начала 2025 года).  
2. В конфигурации для Vertex моделей явно укажите stream\_response: true в litellm\_params, если планируется использование потоковой передачи.  
3. Иногда проблема связана с региональными ограничениями. Попробуйте сменить vertex\_location на us-central1 или us-west1.

### **6.2 Особенности генерации изображений (Nano Banana)**

Генерация изображений через API чата (мультимодальный вход/выход) и через специализированные API (/v1/images/generations) отличается.

* LiteLLM умеет мапить вызовы OpenAI Image API на методы Vertex AI (Imagen/Gemini).  
* Для моделей gemini-3-pro-image-preview важно помнить, что они могут возвращать изображения как base64 или как ссылки (в зависимости от настроек безопасности проекта Google Cloud).  
* Конфигурация 12 показывает, что для редактирования изображений требуются multipart/form-data запросы. Прокси корректно пробрасывает их, но требует достаточного объема оперативной памяти для буферизации больших файлов (до 4K разрешения).

### **6.3 Мониторинг затрат и скидки**

Сниппет 16 упоминает cost\_discount\_config. В корпоративных контрактах с Google часто предусмотрены скидки за объем (Committed Use Discounts). Чтобы LiteLLM корректно отображал затраты в логах и бюджетах, добавьте в config.yaml:

YAML

general\_settings:  
  cost\_discount\_config:  
    vertex\_ai: 0.15 \# 15% скидка по контракту  
    gemini: 0.0 \# Для AI Studio (если платный уровень)

Это позволит финансовому департаменту (FinOps) получать точные данные о потреблении через встроенные метрики LiteLLM (Prometheus/Grafana).

### **6.4 Региональность и Data Residency**

Для европейских компаний критично, чтобы данные не покидали ЕС.

* В конфигурации paid- моделей (Vertex) параметр vertex\_location может быть установлен в europe-west4 (Нидерланды) или europe-west3 (Франкфурт).  
* **Важно:** Preview-модели (например, gemini-3-pro-preview) часто доступны *только* в регионе us-central1 или global на этапе раннего доступа. Это необходимо учитывать при проектировании архитектуры соблюдения нормативных требований (GDPR). Если модель недоступна в Европе, failover на Vertex в США может нарушить комплаенс. В этом случае следует использовать стабильные версии (gemini-2.5-flash), доступные во всех регионах.

### **6.5 Обработка ошибок аутентификации**

Частая ошибка — google.auth.exceptions.DefaultCredentialsError.  
**Причины:**

1. Путь к файлу JSON в переменной GOOGLE\_APPLICATION\_CREDENTIALS неверен внутри контейнера.  
2. У сервисного аккаунта нет прав. Проверьте IAM Policy: аккаунт должен иметь роль Vertex AI User.  
3. Конфликт библиотек: если в окружении присутствуют старые версии google-auth. Использование официального Docker-образа LiteLLM решает эту проблему.

## ---

**7\. Заключение**

Представленная архитектура на базе LiteLLM обеспечивает надежный, экономически эффективный и масштабируемый доступ к передовым моделям Google. Использование гибридного подхода с разделением на Free Tier (AI Studio) и Paid Tier (Vertex AI) позволяет значительно снизить операционные расходы на этапах разработки и тестирования, сохраняя при этом гарантии производительности для продуктивной среды.  
Внедрение механизмов аутентификации OAuth/ADC, несмотря на их сложность, обеспечивает высокий уровень безопасности, исключая необходимость хранения долгоживущих ключей доступа к платным ресурсам в коде приложений. Настройка интеллектуального переключения (fallback) превращает систему в отказоустойчивый шлюз, способный пережить временные ограничения квот без деградации сервиса для конечного пользователя.  
Следуя данному руководству, организации могут построить AI-инфраструктуру, готовую к внедрению моделей следующего поколения, таких как Gemini 3, с минимальными архитектурными изменениями в будущем.  
---

**Таблица 1: Сводная матрица конфигурации моделей**

| Модель (Alias) | Провайдер Primary (Free) | Провайдер Fallback (Paid) | Авторизация Free | Авторизация Paid | Особенности |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Gemini 3 Pro** | AI Studio | Vertex AI | API Key | ADC (Service Account) | Reasoning Level: High |
| **Gemini 3 Flash** | AI Studio | Vertex AI | API Key | ADC (Service Account) | High RPM |
| **Gemini 2.5 Flash** | AI Studio | Vertex AI | API Key | ADC (Service Account) | Stable Baseline |
| **Nano Banana Pro** | AI Studio | Vertex AI | API Key | ADC (Service Account) | Image Gen (4K) |
| **Nano Banana** | AI Studio | Vertex AI | API Key | ADC (Service Account) | Image Gen (Fast) |

#### **Источники**

1. How Application Default Credentials works | Authentication, дата последнего обращения: января 31, 2026, [https://docs.cloud.google.com/docs/authentication/application-default-credentials](https://docs.cloud.google.com/docs/authentication/application-default-credentials)  
2. Authenticate for using client libraries \- Google Cloud Documentation, дата последнего обращения: января 31, 2026, [https://docs.cloud.google.com/docs/authentication/client-libraries](https://docs.cloud.google.com/docs/authentication/client-libraries)  
3. Gemini CLI \- LiteLLM, дата последнего обращения: января 31, 2026, [https://docs.litellm.ai/docs/tutorials/litellm\_gemini\_cli](https://docs.litellm.ai/docs/tutorials/litellm_gemini_cli)  
4. Gemini 3 Pro | Generative AI on Vertex AI, дата последнего обращения: января 31, 2026, [https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-pro](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/gemini/3-pro)  
5. WHEN WILL Gemini 3.0 FINALLY BE RELEASED TO US ?\!, дата последнего обращения: января 31, 2026, [https://discuss.ai.google.dev/t/when-will-gemini-3-0-finally-be-released-to-us/108849](https://discuss.ai.google.dev/t/when-will-gemini-3-0-finally-be-released-to-us/108849)  
6. Gemini \- Google AI Studio \- LiteLLM, дата последнего обращения: января 31, 2026, [https://docs.litellm.ai/docs/providers/gemini](https://docs.litellm.ai/docs/providers/gemini)  
7. Gemini 3 Developer Guide | Gemini API \- Google AI for Developers, дата последнего обращения: января 31, 2026, [https://ai.google.dev/gemini-api/docs/gemini-3](https://ai.google.dev/gemini-api/docs/gemini-3)  
8. Gemini 3 Flash: frontier intelligence built for speed \- Google Blog, дата последнего обращения: января 31, 2026, [https://blog.google/products-and-platforms/products/gemini/gemini-3-flash/](https://blog.google/products-and-platforms/products/gemini/gemini-3-flash/)  
9. Nano Banana image generation | Gemini API, дата последнего обращения: января 31, 2026, [https://ai.google.dev/gemini-api/docs/image-generation](https://ai.google.dev/gemini-api/docs/image-generation)  
10. Introducing Nano Banana Pro \- Google Blog, дата последнего обращения: января 31, 2026, [https://blog.google/innovation-and-ai/products/nano-banana-pro/](https://blog.google/innovation-and-ai/products/nano-banana-pro/)  
11. Learn about supported models | Firebase AI Logic, дата последнего обращения: января 31, 2026, [https://firebase.google.com/docs/ai-logic/models](https://firebase.google.com/docs/ai-logic/models)  
12. /images/edits | liteLLM, дата последнего обращения: января 31, 2026, [https://docs.litellm.ai/docs/image\_edits](https://docs.litellm.ai/docs/image_edits)  
13. Introducing Gemini 2.5 Flash Image, our state-of-the-art image model, дата последнего обращения: января 31, 2026, [https://developers.googleblog.com/introducing-gemini-2-5-flash-image/](https://developers.googleblog.com/introducing-gemini-2-5-flash-image/)  
14. \[Bug\]: LiteLLM does not authenticate Gemini with API key. Asking for ..., дата последнего обращения: января 31, 2026, [https://github.com/BerriAI/litellm/issues/14771](https://github.com/BerriAI/litellm/issues/14771)  
15. \[Bug\]: · Issue \#18890 · BerriAI/litellm \- GitHub, дата последнего обращения: января 31, 2026, [https://github.com/BerriAI/litellm/issues/18890](https://github.com/BerriAI/litellm/issues/18890)  
16. Provider Discounts \- LiteLLM, дата последнего обращения: января 31, 2026, [https://docs.litellm.ai/docs/proxy/provider\_discounts](https://docs.litellm.ai/docs/proxy/provider_discounts)
# **Архитектурная интеграция Gemini в экосистему OpenAPI: Управление квотами, мультипрофильная конфигурация и доступ к специализированным моделям**

## **1\. Введение: Парадигма унификации интерфейсов генеративного ИИ**

В современной разработке интеллектуальных систем наблюдается фундаментальный сдвиг от использования проприетарных SDK (Software Development Kits) к стандартизированным протоколам взаимодействия. Задача интеграции моделей Google Gemini в архитектуру, использующую стиль запросов OpenAPI (де-факто стандарт, популяризированный OpenAI), представляет собой не просто вопрос удобства синтаксиса, но и стратегическое решение по обеспечению переносимости кода, модульности и гибкости инфраструктуры. Пользовательский запрос, касающийся отказа от концепции "memory bank" в пользу создания надежного API-шлюза для Gemini, отражает зрелый инженерный подход, требующий глубокого анализа механизмов биллинга, конфигурационного управления и доступа к моделям.  
Данный отчет представляет собой исчерпывающее техническое руководство и аналитическое исследование, направленное на решение трех ключевых задач: определение механики списания средств (квоты против кредитов), архитектурное проектирование мультипрофильных конфигураций для новейших моделей (Gemini 3 Pro/Flash) и реализация доступа к специализированным моделям ("Nano Banana") через унифицированный интерфейс. Анализ базируется на детальном изучении технической документации Google Cloud, Vertex AI и архитектурных паттернов использования прокси-серверов (LiteLLM).  
Переход к OpenAPI-совместимому слою для Gemini требует внедрения промежуточного программного обеспечения — прокси-сервера, который выполняет трансляцию запросов формата Chat Completions API в нативные вызовы Vertex AI или Google AI Studio. Этот архитектурный паттерн, известный как "AI Gateway", позволяет абстрагироваться от специфики провайдера, однако вносит существенные нюансы в управление идентификацией и биллингом. В контексте Google Cloud это означает необходимость четкого разграничения между "потребительским" уровнем доступа (API Key) и "корпоративным" уровнем (IAM), что напрямую влияет на то, будет ли использоваться бесплатная квота или предоплаченные кредиты Vertex AI.

## **2\. Экономическая архитектура Gemini CLI: Квоты против Кредитов Vertex AI**

Первый и наиболее критичный вопрос касается механики потребления ресурсов при использовании Gemini CLI. Понимание того, какой именно ресурс расходуется — бесплатная дневная квота или денежные кредиты из подписки Google AI Premium — требует глубокого погружения в систему аутентификации Google.

### **2.1 Дихотомия биллинга: API Key против IAM**

Экосистема Gemini функционирует в двух параллельных экономических реальностях, выбор между которыми определяется исключительно методом аутентификации, используемым в момент инициализации сессии CLI. В отличие от многих других платформ, где тарифный план привязан к аккаунту, в Google Cloud источник финансирования запроса определяется *типом учетных данных*.

#### **2.1.1 Режим бесплатной квоты (Consumer Tier)**

При стандартной настройке Gemini CLI, когда пользователь генерирует API-ключ через Google AI Studio и экспортирует его как переменную окружения GEMINI\_API\_KEY (или настраивает через gemini configure), система по умолчанию использует "Потребительский уровень" (Consumer Tier).  
Технический анализ показывает, что в этом режиме действуют следующие ограничения и правила:

* **Лимиты запросов:** Пользователям предоставляется щедрая, но жесткая квота. Для модели Gemini 2.5 Pro (и последующих версий) это, как правило, 1000 запросов в день бесплатно.1 Для более легковесных моделей, таких как Flash, лимиты могут быть выше (до 1500 запросов), но они конечны.  
* **Механизм списания:** В этом режиме *финансовые средства не затрагиваются*. Кредиты Vertex AI (те самые $10) **не используются**. Система работает по принципу "use it or lose it" в рамках суточного цикла.  
* **Ограничение:** Как только лимит в 1000-1500 запросов исчерпан, API начинает возвращать ошибки 429 Too Many Requests, и работа блокируется до следующего календарного дня. Никакого автоматического переключения на платный аккаунт или использование кредитов не происходит.3

#### **2.1.2 Режим Vertex AI (Enterprise/Subscription Tier)**

Для того чтобы задействовать кредиты Vertex AI в размере $10, входящие в подписку Google AI Premium (или эквивалентные бонусы для разработчиков), необходимо фундаментально изменить способ взаимодействия CLI с облаком. Gemini CLI не "узнает" о наличии подписки через простой API-ключ AI Studio.  
Чтобы активировать использование кредитов, необходимо перевести CLI в режим работы с Vertex AI. Это достигается через механизм Application Default Credentials (ADC) и переменную окружения GOOGLE\_GENAI\_USE\_VERTEXAI.  
**Алгоритм активации кредитов:**

1. Вместо GEMINI\_API\_KEY используется аутентификация через Google Cloud CLI (gcloud auth login или сервисный аккаунт).  
2. Устанавливается флаг export GOOGLE\_GENAI\_USE\_VERTEXAI=true.4  
3. Запросы маршрутизируются не в публичный API AI Studio, а в endpoint Vertex AI (us-central1-aiplatform.googleapis.com).

**Финансовая механика использования $10:**  
В этом режиме понятие "бесплатной квоты в запросах" исчезает. Вместо этого действует модель "Pay-as-you-go" (оплата за использование).

* Каждый запрос тарифицируется по прейскуранту Vertex AI (например, $0.00125 за 1000 символов ввода для Pro-моделей).3  
* Эти расходы аккумулируются в биллинговом аккаунте Google Cloud, привязанном к проекту.  
* Кредит в $10, предоставляемый в рамках подписки, автоматически применяется к этому биллинговому аккаунту в конце отчетного периода, покрывая расходы на генеративный ИИ.5

### **2.2 Ответ на Вопрос 1**

Таким образом, прямой ответ на первый вопрос пользователя является многосоставным и зависит от конфигурации:  
Gemini CLI **не будет автоматически использовать** кредиты Vertex ($10), если вы просто используете API-ключ. В стандартной конфигурации он будет расходовать вашу бесплатную квоту (1500 запросов/день).  
Чтобы задействовать $10 кредитов Vertex AI, вы **обязаны** переконфигурировать CLI на использование Vertex AI backend. Это требует наличия Google Cloud Project, привязки биллинга и использования аутентификации через gcloud (IAM), а не через API Key. В этом случае лимит в 1500 запросов снимается, и вы переходите на тарификацию за токены, которая покрывается вашими кредитами.4

## ---

**3\. Архитектура Мультипрофильной Конфигурации Моделей**

Второй вопрос пользователя касается возможности создания нескольких конфигураций для различных моделей Google, таких как Gemini 3 Pro Preview и Gemini 3 Flash Preview. Это критически важно для эффективной разработки, позволяя переключаться между "дорогой и умной" моделью для сложных задач и "быстрой и дешевой" для рутинных операций. Исследование подтверждает, что экосистема Gemini предоставляет гибкие инструменты для реализации такой архитектуры, как на уровне нативного CLI, так и через прокси-слой LiteLLM.

### **3.1 Управление конфигурациями в нативном Gemini CLI**

Gemini CLI поддерживает иерархическую систему конфигурации, которая позволяет переопределять параметры на уровне системы, пользователя, проекта и конкретной команды запуска. Это обеспечивает возможность создания изолированных профилей.

#### **3.1.1 Проектная изоляция через settings.json**

Наиболее надежный способ управления разными моделями — использование проектных файлов конфигурации. Gemini CLI ищет файл .gemini/settings.json в корневой директории текущего проекта.8  
Это позволяет создать следующую структуру папок для разных "профилей":

* **Профиль "Pro" (для сложных вычислений):**  
  Директория: \~/dev/gemini-pro-env/  
  Файл .gemini/settings.json:  
  JSON  
  {  
    "model": "gemini-3-pro-preview",  
    "temperature": 0.7,  
    "maxOutputTokens": 8192,  
    "vertex": {  
      "project": "my-pro-billing-project",  
      "location": "us-central1"  
    }  
  }

* **Профиль "Flash" (для быстрых итераций):**  
  Директория: \~/dev/gemini-flash-env/  
  Файл .gemini/settings.json:  
  JSON  
  {  
    "model": "gemini-3-flash-preview",  
    "temperature": 0.2,  
    "vertex": {  
      "project": "my-flash-billing-project",  
      "location": "us-west1"  
    }  
  }

При запуске команды gemini из соответствующей директории CLI автоматически подгружает нужную модель и настройки биллинга.9

#### **3.1.2 Динамическое переключение через флаги**

Для более оперативного переключения без смены директорий Gemini CLI поддерживает флаг \--model. Это позволяет использовать одну базовую конфигурацию, но переопределять модель "на лету".7

Bash

\# Запуск с моделью Flash (например, для проверки синтаксиса)  
gemini prompt "Проверь этот код" \--model gemini-3-flash-preview

\# Запуск с моделью Pro (для рефакторинга архитектуры)  
gemini prompt "Оптимизируй этот класс" \--model gemini-3-pro-preview

### **3.2 Реализация мультипрофильности в OpenAPI-прокси (LiteLLM)**

Поскольку основная цель пользователя — создание "OpenAPI подобного стиля API запросов", наиболее элегантное решение заключается в конфигурации прокси-сервера LiteLLM. Этот подход позволяет определить **Алиасы (Псевдонимы)** моделей. Вы можете определить собственные названия моделей в конфигурационном файле прокси, которые будут маппиться на конкретные версии моделей Google и настройки Vertex AI.

#### **3.2.1 Конфигурация config.yaml для LiteLLM**

В файле конфигурации LiteLLM (config.yaml) можно задать список моделей (model\_list), каждая из которых будет иметь уникальный идентификатор для вызова через API, но ссылаться на разные бекенды Google.10  
Пример конфигурации для реализации запроса пользователя:

YAML

model\_list:  
  \# Конфигурация 1: Gemini 3 Pro Preview (Псевдоним: "gpt-pro")  
  \- model\_name: gpt-pro  
    litellm\_params:  
      model: vertex\_ai/gemini-3-pro-preview  
      vertex\_project: "my-main-project-id"  \# Проект с привязанными кредитами $10  
      vertex\_location: "us-central1"  
      rpm: 60  \# Лимит запросов в минуту для этой модели

  \# Конфигурация 2: Gemini 3 Flash Preview (Псевдоним: "gpt-flash")  
  \- model\_name: gpt-flash  
    litellm\_params:  
      model: vertex\_ai/gemini-3-flash-preview  
      vertex\_project: "my-main-project-id"  
      vertex\_location: "us-central1"

  \# Конфигурация 3: Экспериментальная модель (Псевдоним: "gpt-legacy")  
  \- model\_name: gpt-legacy  
    litellm\_params:  
      model: vertex\_ai/gemini-1.5-pro  
      vertex\_project: "my-backup-project-id"

**Преимущества подхода:**

1. **Унификация:** Клиентское приложение всегда обращается к http://localhost:4000/v1/chat/completions.  
2. **Гибкость:** В поле model запроса вы передаете gpt-pro или gpt-flash. Прокси сам решает, куда направить запрос, какие учетные данные использовать и к какому проекту Vertex AI обратиться.  
3. **Безопасность:** Учетные данные и ID проектов скрыты внутри конфигурации прокси и не передаются в клиентском коде.

### **3.3 Ответ на Вопрос 2**

Да, вы абсолютно точно можете создать несколько конфигураций под разные модели Google.

* В **Gemini CLI** это делается либо через создание разных директорий с файлами .gemini/settings.json, либо через использование флага \--model при запуске.  
* В **OpenAPI-прокси (LiteLLM)** это реализуется через секцию model\_list в config.yaml, где вы создаете виртуальные имена (алиасы) для каждой нужной вам модели (Gemini 3 Pro, Flash и т.д.) и привязываете их к соответствующим параметрам Vertex AI.

## ---

**4\. Интеграция Специализированных Моделей: Кейс "Nano Banana"**

Третий вопрос касается возможности использования моделей, которые официально не представлены в меню Gemini CLI, в частности, модели "Nano Banana", и возможности оплаты их использования через кредиты Vertex AI ($10). Это требует детального анализа природы модели "Nano Banana" и технических возможностей Vertex AI API.

### **4.1 Идентификация модели "Nano Banana"**

На основе проанализированных данных, "Nano Banana" — это маркетинговое или внутреннее кодовое название для модели **Gemini 2.5 Flash Image** (технический идентификатор: gemini-2.5-flash-image или gemini-2.5-flash-image-preview).12 Это специализированная мультимодальная модель, оптимизированная для генерации изображений с высокой точностью рендеринга текста и редактирования существующих изображений.  
Ключевая особенность этой модели — она *нативная* (native multimodal), то есть обучалась одновременно на тексте и изображениях, что отличает ее от моделей, использующих отдельные инструменты (tools) для генерации картинок (как, например, DALL-E 3 в ChatGPT, который работает через вызов инструмента).

### **4.2 Доступность через Vertex AI и Кредиты**

Поскольку "Nano Banana" (Gemini 2.5 Flash Image) является частью семейства моделей, доступных в **Vertex AI Model Garden**, на нее распространяются стандартные правила биллинга Vertex AI.15

* **Использование кредитов:** Да, вы можете использовать свои $10 кредитов Vertex AI для оплаты вызовов к этой модели.  
* **Стоимость:** Модель тарифицируется за количество выходных токенов или за сгенерированное изображение. Согласно данным, стоимость составляет около **$0.039 за изображение** (примерно 3.9 цента).14 Это означает, что $10 кредитов позволят сгенерировать примерно **256 изображений** в месяц при условии отсутствия других расходов.

### **4.3 Техническая реализация доступа (CLI vs Proxy)**

Здесь возникает важное архитектурное различие. Gemini CLI — это *текстовый* агент. Хотя он может принимать изображения на вход (мультимодальный ввод), он не спроектирован как инструмент для вывода бинарных данных (сгенерированных изображений) в терминал. Поэтому "Nano Banana" может не поддерживаться в CLI "из коробки" как модель для чата.  
Однако, ваша цель — "OpenAPI подобный стиль". И здесь возможности LiteLLM позволяют интегрировать эту модель бесшовно.

#### **4.3.1 Интеграция "Nano Banana" в LiteLLM**

LiteLLM поддерживает проксирование запросов к моделям генерации изображений Vertex AI, транслируя их в формат OpenAI Image Generation API (/v1/images/generations) или обрабатывая как специфический тип чат-запроса.13  
**Конфигурация в config.yaml для "Nano Banana":**

YAML

model\_list:  
  \- model\_name: nano-banana  
    litellm\_params:  
      model: vertex\_ai/gemini-2.5-flash-image  
      vertex\_project: "your-project-id"  
      vertex\_location: "us-central1"  
      \# Параметры для маппинга специфики генерации изображений  
      modality: "image" 

После такой настройки вы сможете обращаться к модели через стандартный curl запрос, используя свои кредиты:

Bash

curl http://localhost:4000/v1/chat/completions \\  
  \-H "Content-Type: application/json" \\  
  \-H "Authorization: Bearer sk-1234" \\  
  \-d '{  
    "model": "nano-banana",  
    "messages": \[  
      {"role": "user", "content": "Create a futuristic banana logo with text 'Nano'"}  
    \]  
  }'

*Примечание: В зависимости от версии LiteLLM, для генерации изображений может потребоваться использование эндпоинта /v1/images/generations или передача специфических флагов в теле сообщения, так как модель возвращает не текст, а ссылку на изображение или base64 код.*

### **4.4 Ответ на Вопрос 3**

Да, вы можете использовать модели, которых нет в стандартном меню Gemini CLI, включая "Nano Banana" (Gemini 2.5 Flash Image).

* **Через Vertex AI:** Эта модель доступна в Vertex AI API, и ее использование **покрывается вашими $10 кредитами**.  
* **Через CLI:** Прямое использование в CLI может быть ограничено из\-за специфики вывода (изображения), но технически возможно через вызов API.  
* **Через ваш OpenAPI-прокси:** Это наиболее рекомендуемый путь. Вы добавляете модель в конфигурацию LiteLLM, указывая ее техническое имя gemini-2.5-flash-image, и получаете доступ к ней через стандартный API-интерфейс, расходуя кредиты Vertex.

## ---

**5\. Полное Руководство по Настройке (Implementation Guide)**

Ниже приведена пошаговая инструкция по реализации всей описанной архитектуры, интегрирующая ответы на все три вопроса.

### **Шаг 1: Подготовка среды Vertex AI (Активация Кредитов)**

Чтобы Gemini CLI и прокси использовали $10 кредитов вместо бесплатной квоты:

1. **Создайте проект в Google Cloud Console.**  
2. **Привяжите биллинг:** Убедитесь, что к проекту привязан биллинг-аккаунт, на котором активна подписка с кредитами.  
3. **Включите Vertex AI API:** В библиотеке API найдите и включите "Vertex AI API".  
4. **Установите Google Cloud SDK** на локальной машине и авторизуйтесь:  
   Bash  
   gcloud auth login  
   gcloud config set project  
   gcloud auth application-default login

   Это создаст файл application\_default\_credentials.json (ADC), который будет ключом к использованию кредитов.18

### **Шаг 2: Настройка Docker-контейнера LiteLLM (OpenAPI Proxy)**

Мы используем Docker для создания стабильной среды, которая имеет доступ к вашим локальным кредешиалам (для оплаты кредитами) и настроена на несколько моделей.  
**Файл docker-compose.yml:**

YAML

version: '3.8'

services:  
  gemini-proxy:  
    image: ghcr.io/berriai/litellm:main-latest  
    container\_name: gemini-openai-adapter  
    ports:  
      \- "4000:4000"  
    volumes:  
      \# Монтируем конфигурацию моделей  
      \-./litellm-config.yaml:/app/config.yaml  
      \# Монтируем кредешиалы Google Cloud для доступа к Vertex AI (и кредитам)  
      \# Путь \~/.config/gcloud/application\_default\_credentials.json зависит от вашей ОС  
      \- \~/.config/gcloud/application\_default\_credentials.json:/app/application\_default\_credentials.json:ro  
    environment:  
      \# Указываем прокси, где искать ключи внутри контейнера  
      \- GOOGLE\_APPLICATION\_CREDENTIALS=/app/application\_default\_credentials.json  
      \# Мастер-ключ для защиты вашего прокси (как API Key OpenAI)  
      \- LITELLM\_MASTER\_KEY=sk-my-secret-key-123  
    command: \[ "--config", "/app/config.yaml", "--detailed\_debug" \]

### **Шаг 3: Создание конфигурации моделей (litellm-config.yaml)**

Здесь мы реализуем мультипрофильность и добавляем "Nano Banana".

YAML

model\_list:  
  \# 1\. Основная мощная модель (Gemini 3 Pro Preview)  
  \# Будет использовать кредиты Vertex AI  
  \- model\_name: gemini-3-pro  
    litellm\_params:  
      model: vertex\_ai/gemini-3-pro-preview  
      vertex\_project: "your-project-id"  
      vertex\_location: "us-central1"

  \# 2\. Быстрая модель (Gemini 3 Flash Preview)  
  \# Также использует кредиты Vertex AI  
  \- model\_name: gemini-3-flash  
    litellm\_params:  
      model: vertex\_ai/gemini-3-flash-preview  
      vertex\_project: "your-project-id"  
      vertex\_location: "us-central1"

  \# 3\. Специфическая модель "Nano Banana" (Gemini 2.5 Flash Image)  
  \# Доступна через Vertex, оплачивается кредитами  
  \- model\_name: nano-banana  
    litellm\_params:  
      model: vertex\_ai/gemini-2.5-flash-image  
      vertex\_project: "your-project-id"  
      vertex\_location: "us-central1"

litellm\_settings:  
  drop\_params: true  \# Удаляет параметры, не поддерживаемые Vertex, чтобы избежать ошибок

### **Шаг 4: Тестирование и Использование**

Теперь у вас запущен локальный сервер на порту 4000, который полностью имитирует OpenAI API, но все запросы направляет в Google Vertex AI, используя ваши $10 кредитов.  
**Пример запроса к "Nano Banana" (Bash):**

Bash

curl http://localhost:4000/v1/chat/completions \\  
  \-H "Content-Type: application/json" \\  
  \-H "Authorization: Bearer sk-my-secret-key-123" \\  
  \-d '{  
    "model": "nano-banana",  
    "messages":  
  }'

**Пример запроса к Gemini 3 Pro (Python):**

Python

from openai import OpenAI

client \= OpenAI(  
    api\_key="sk-my-secret-key-123",  
    base\_url="http://localhost:4000/v1"  
)

response \= client.chat.completions.create(  
    model="gemini-3-pro",  
    messages=\[{"role": "user", "content": "Explain quantum computing"}\]  
)  
print(response.choices.message.content)

## **6\. Заключение и Аналитические Выводы**

Проведенный анализ позволяет сформировать четкую стратегию для реализации вашего проекта. Переход к использованию Gemini через OpenAPI-совместимый слой является технически обоснованным и реализуемым решением, которое предоставляет полный контроль над расходами и конфигурацией.

1. **Управление бюджетом:** Ключевым фактором является выбор метода аутентификации. Использование GEMINI\_API\_KEY удерживает вас в рамках бесплатной квоты (1500 запросов), в то время как переход на ADC (Application Default Credentials) через прокси открывает доступ к кредитам Vertex AI ($10) и снимает жесткие лимиты по количеству запросов.  
2. **Гибкость конфигурации:** Архитектура на базе LiteLLM позволяет создавать неограниченное количество профилей моделей (алиасов), что решает задачу разделения конфигураций для Gemini 3 Pro, Flash и других версий. Это значительно превосходит возможности нативного CLI по удобству интеграции в код.  
3. **Доступ к скрытым возможностям:** Модели типа "Nano Banana" (Gemini 2.5 Flash Image) не являются закрытыми; они просто требуют правильного обращения через API Vertex AI. Использование прокси позволяет "легализовать" их использование в стандартном пайплайне разработки, оплачивая их ресурсами из подписки.

Рекомендуемая архитектура с использованием Docker-контейнера LiteLLM, смонтированными учетными данными Google Cloud и детально настроенным файлом config.yaml полностью удовлетворяет всем поставленным требованиям, обеспечивая масштабируемость, предсказуемость расходов и доступ к передовым мультимодальным возможностям Google.

#### **Источники**

1. Gemini CLI: your open-source AI agent \- Google Blog, дата последнего обращения: января 31, 2026, [https://blog.google/innovation-and-ai/technology/developers-tools/introducing-gemini-cli-open-source-ai-agent/](https://blog.google/innovation-and-ai/technology/developers-tools/introducing-gemini-cli-open-source-ai-agent/)  
2. Are there usage limits or rate limits on Gemini CLI? \- Milvus, дата последнего обращения: января 31, 2026, [https://milvus.io/ai-quick-reference/are-there-usage-limits-or-rate-limits-on-gemini-cli](https://milvus.io/ai-quick-reference/are-there-usage-limits-or-rate-limits-on-gemini-cli)  
3. Gemini CLI: Quotas and pricing, дата последнего обращения: января 31, 2026, [https://geminicli.com/docs/quota-and-pricing/](https://geminicli.com/docs/quota-and-pricing/)  
4. How do I authenticate with Google to use Gemini CLI? \- Milvus, дата последнего обращения: января 31, 2026, [https://milvus.io/ai-quick-reference/how-do-i-authenticate-with-google-to-use-gemini-cli](https://milvus.io/ai-quick-reference/how-do-i-authenticate-with-google-to-use-gemini-cli)  
5. Google Developer Program Benefits FAQ, дата последнего обращения: января 31, 2026, [https://developers.google.com/profile/help/benefits](https://developers.google.com/profile/help/benefits)  
6. Google bundles developer perks into AI subscriptions, дата последнего обращения: января 31, 2026, [https://www.techbuzz.ai/articles/google-bundles-developer-perks-into-ai-subscriptions](https://www.techbuzz.ai/articles/google-bundles-developer-perks-into-ai-subscriptions)  
7. How do I switch models in Gemini CLI? \- Milvus, дата последнего обращения: января 31, 2026, [https://milvus.io/ai-quick-reference/how-do-i-switch-models-in-gemini-cli](https://milvus.io/ai-quick-reference/how-do-i-switch-models-in-gemini-cli)  
8. Hands-on with Gemini CLI \- Google Codelabs, дата последнего обращения: января 31, 2026, [https://codelabs.developers.google.com/gemini-cli-hands-on](https://codelabs.developers.google.com/gemini-cli-hands-on)  
9. Where are the Gemini CLI config files stored? \- Milvus, дата последнего обращения: января 31, 2026, [https://milvus.io/ai-quick-reference/where-are-the-gemini-cli-config-files-stored](https://milvus.io/ai-quick-reference/where-are-the-gemini-cli-config-files-stored)  
10. Build with your Favorite Models from the Vertex AI Model Garden ..., дата последнего обращения: января 31, 2026, [https://medium.com/google-cloud/build-with-your-favorite-models-from-the-vertex-ai-model-garden-with-litellm-0b140bf52a01](https://medium.com/google-cloud/build-with-your-favorite-models-from-the-vertex-ai-model-garden-with-litellm-0b140bf52a01)  
11. \[BETA\] LiteLLM Managed Files, дата последнего обращения: января 31, 2026, [https://docs.litellm.ai/docs/proxy/litellm\_managed\_files](https://docs.litellm.ai/docs/proxy/litellm_managed_files)  
12. How Nano Banana got its name \- Google Blog, дата последнего обращения: января 31, 2026, [https://blog.google/products-and-platforms/products/gemini/how-nano-banana-got-its-name/](https://blog.google/products-and-platforms/products/gemini/how-nano-banana-got-its-name/)  
13. Nano Banana image generation | Gemini API, дата последнего обращения: января 31, 2026, [https://ai.google.dev/gemini-api/docs/image-generation](https://ai.google.dev/gemini-api/docs/image-generation)  
14. Introducing Gemini 2.5 Flash Image, our state-of-the-art image ..., дата последнего обращения: января 31, 2026, [https://developers.googleblog.com/introducing-gemini-2-5-flash-image/](https://developers.googleblog.com/introducing-gemini-2-5-flash-image/)  
15. Nano Banana Pro available for enterprise | Google Cloud Blog, дата последнего обращения: января 31, 2026, [https://cloud.google.com/blog/products/ai-machine-learning/nano-banana-pro-available-for-enterprise](https://cloud.google.com/blog/products/ai-machine-learning/nano-banana-pro-available-for-enterprise)  
16. Use Gemini 2.5 Flash Image (nano banana) on Vertex AI, дата последнего обращения: января 31, 2026, [https://cloud.google.com/blog/products/ai-machine-learning/gemini-2-5-flash-image-on-vertex-ai](https://cloud.google.com/blog/products/ai-machine-learning/gemini-2-5-flash-image-on-vertex-ai)  
17. Google AI Studio Image Generation \- LiteLLM, дата последнего обращения: января 31, 2026, [https://docs.litellm.ai/docs/providers/google\_ai\_studio/image\_gen](https://docs.litellm.ai/docs/providers/google_ai_studio/image_gen)  
18. How Application Default Credentials works | Authentication, дата последнего обращения: января 31, 2026, [https://docs.cloud.google.com/docs/authentication/application-default-credentials](https://docs.cloud.google.com/docs/authentication/application-default-credentials)
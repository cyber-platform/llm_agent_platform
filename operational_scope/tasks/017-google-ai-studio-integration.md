# Task: Интеграция Google AI studio

## Контекст

Добавляем нового провайдера в сервис — Google AI studio.

Для реализации поддержки провайдера мы используем официальную библиотеку для Python.

```
from google import genai
```

Данный провайдер в качестве creds использует официальные Gemini API-ключи.

Реализуем через genai ту же логику по которой сейчас работает gemini cli.

Поддерживаемые модели:
- gemini-3.1-flash-lite-preview
- gemini-3-flash-preview
- gemini-2.5-pro

Реализуем только работу с самими моделями без использования особых инструментов от Google.

Requests per day (RPD) quotas reset at midnight Pacific time.

Можно рассмотреть добавление опции сброса квот по времени.

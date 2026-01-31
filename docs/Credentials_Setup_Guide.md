# Руководство по настройке ключей доступа (Credentials)

Для работы гибридного прокси требуются два типа учетных данных.

## 1. Настройка для Quota / Google AI Pro (Бесплатные лимиты)
**Цель:** Получить файл `secrets/user_credentials.json`.
**Используется для:** Профилей `gemini-*-quota`.

Этот метод использует эмуляцию **Gemini CLI** для доступа к расширенным квотам вашей подписки (1500+ запросов в день).

### Шаги:
1.  Убедитесь, что у вас установлен Python и необходимые библиотеки:
    ```bash
    pip install google-auth-oauthlib
    ```

2.  Запустите наш специальный скрипт авторизации:
    ```bash
    python3 scripts/get_oauth_credentials.py
    ```

3.  **Что произойдет:**
    *   Скрипт откроет ссылку в браузере для входа в Google.
    *   Вы увидите запрос на авторизацию от приложения **"Google Cloud Code"** (или похожего официального инструмента). Это нормально — мы используем их публичный Client ID.
    *   После подтверждения скрипт сохранит токены в `secrets/user_credentials.json`.

**ВНИМАНИЕ:** Вам НЕ нужно создавать свой собственный проект в Google Cloud Console или скачивать `client_secret.json`. Мы используем официальные идентификаторы Google для доступа к правильным квотам.

### Проверка работы с Kilo Code
После получения `user_credentials.json` и запуска прокси, вы можете сразу подключить его в Kilo Code:
- **Provider:** OpenAI Compatible
- **Base URL:** `http://localhost:4000/v1`
- **API Key:** `sk-proxy` (или любой другой)
- **Model:** `gemini-3-flash-preview-quota`

---

## 2. Настройка для Vertex AI (Платные кредиты)
**Цель:** Получить файл `secrets/service_account.json`.
**Используется для:** Профилей `gemini-*-vertex`.

Используйте этот метод, только если вы хотите тратить свои $10/мес облачных кредитов.

1.  **Откройте Google Cloud Console:**
    Перейдите в раздел [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts).

2.  **Создайте сервисный аккаунт:**
    *   Нажмите **+ CREATE SERVICE ACCOUNT**.
    *   Имя: `litellm-proxy`.

3.  **Назначьте роль:**
    *   Выберите роль **Vertex AI User**.

4.  **Создайте ключ:**
    *   В списке аккаунтов нажмите Actions -> **Manage keys**.
    *   **ADD KEY** -> **Create new key** (JSON).

5.  **Сохраните файл:**
    *   Переименуйте скачанный файл в `service_account.json`.
    *   Положите его в папку `secrets/` проекта.
    *   В файле `.env` укажите `VERTEX_PROJECT_ID` и `VERTEX_LOCATION`.
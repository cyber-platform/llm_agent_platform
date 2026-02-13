# Task: Infrastructure and Configuration Refactoring

## Контекст
Проект содержит хардкод секретов и конфигурации в `config.py`. Необходимо перенести все настройки в переменные окружения и настроить тестовую среду.

## Шаги реализации
1.  Создать `.env.example` со всеми необходимыми переменными:
    *   `GEMINI_CLI_CLIENT_ID`
    *   `GEMINI_CLI_CLIENT_SECRET`
    *   `VERTEX_PROJECT_ID`
    *   `VERTEX_LOCATION`
    *   `DEFAULT_MODEL`
2.  Обновить `config.py` для чтения из `os.environ`.
3.  Настроить `pytest`:
    *   Создать `tests/conftest.py`.
    *   Написать первый unit-тест для `api/openai/transform.py`.
4.  Добавить `python-dotenv` в зависимости (через `uv`).

## Критерии готовности
- [ ] Файл `.env.example` создан.
- [ ] `config.py` не содержит секретов.
- [ ] Команда `pytest` запускается и проходит (хотя бы один тест).
- [ ] Проект запускается с использованием переменных окружения.

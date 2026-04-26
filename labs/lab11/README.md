# Lab 11: LLM Extraction & Schema-First Pipeline

Цей репозиторій містить реалізацію автоматизованого пайплайну для витягування структурованих метаданих із сирих текстових описів датасетів.

## 1. Обраний Extraction-кейс
**Домен:** Каталог відкритих даних України (UA Datasets).
**Завдання:** Перетворення неструктурованих описів наборів даних (з порталів, GitHub, новин) у чіткий структурований формат для подальшого імпорту в бази даних (Data Catalog).

## 2. JSON Schema
Для суворого контролю типів використовується схема з обов'язковими полями. 
Основні вимоги:
* `record_count`: суворо `integer` або `null`.
* `access_level`: суворо Enum (`public`, `upon_request`, `commercial`).
* Відсутні значення повинні повертатися як `null`, а не вигадані рядки.

""" + json_code + """{
  "type": "object",
  "properties": {
    "dataset_title": {"type": "string"},
    "data_types": {"type": "array", "items": {"type": "string"}},
    "record_count": {"type": ["integer", "null"]},
    "file_formats": {"type": "array", "items": {"type": "string"}},
    "access_level": {"type": "string", "enum": ["public", "upon_request", "commercial"]},
    "license": {"type": ["string", "null"]}
  },
  "required": ["dataset_title", "data_types", "record_count", "file_formats", "access_level", "license"]
}
""" + md_code + """

## 3. Baseline Prompt
Базовий промпт побудований за принципом System-Role + Schema Injection:

""" + txt_code + """SYSTEM: You are a strict data extraction system. Your exact task is to extract information from the user's text and return it matching the JSON schema below.

JSON SCHEMA:
{...schema...}

INSTRUCTIONS:
1. Return ONLY valid JSON.
2. No markdown formatting (no ```json).
3. No conversational text.
4. If a field is missing, use null.

USER TEXT:
{text}
""" + md_code + """

## 4. Використаний Validator
В якості валідатора використовується стандартна Python-бібліотека `jsonschema`. 
Вона виконує дві функції:
1. Синтаксична перевірка (чи є відповідь валідним JSON-об'єктом).
2. Семантична перевірка (відповідність типів, наявність required полів, дотримання Enum).

## 5. Механізм самокорекції (Repair Loop)
Реалізовано Fail-Safe патерн для захисту від галюцинацій LLM:
1. Якщо `jsonschema` кидає помилку (наприклад, `ValidationError: '10k' is not of type 'integer'`), пайплайн перехоплює її.
2. Формується **Repair Prompt**, який відправляється назад у LLM: *"Твій попередній вихід впав з помилкою: [текст помилки]. Виправ свій JSON."*
3. Ліміт: Максимум 2 спроби виправлення (Circuit Breaker), щоб уникнути нескінченних запитів.

## 6. Valid JSON Rate (Метрики успішності)
Під час тестування на новому SDK `google-genai` та моделі `gemini-2.5-flash` отримано наступні результати:
* **Raw valid JSON rate:** 100.0% (Відсутність markdown-сміття).
* **Schema-valid JSON rate (до Repair Loop):** 100.0% (Модель ідеально нормалізує числа та дотримується Enum).
* **Post-repair valid JSON rate (після Repair Loop):** 100.0%.

*Примітка: Високий показник з 1-ї спроби зумовлений потужністю моделі покоління 2.5. На старіших моделях (1.5 Flash) показник успішності до Repair Loop складав ~40%, що доводило необхідність механізму самокорекції.*

## 7. Які проблеми залишаються у Production
Незважаючи на 100% точність на тестовій вибірці, при масштабуванні залишаються архітектурні виклики:
1. **API Rate Limits:** Безкоштовні API-ключі мають жорсткі ліміти (Quota Exceeded). При швидкій пакетній обробці сервер відкидає запити, що вимагає імплементації експоненційної затримки (Exponential Backoff).
2. **Null Aversion:** LLM психологічно "не люблять" повертати `null`. При недостатньо жорсткому промпті вони можуть генерувати галюцинації (наприклад, вигадувати ліцензії), щоб заповнити порожнечу.
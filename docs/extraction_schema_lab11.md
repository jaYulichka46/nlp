# Extraction Schema Specification: Lab 11

Цей документ описує архітектуру екстракції метаданих для проєкту **UA Datasets** — каталогу відкритих даних України.

## 1. Екстракційна задача (Task Description)
**Мета:** Перетворити неструктуровані текстові описи наборів даних (з порталів open data, GitHub, Kaggle) у валідний JSON-об'єкт.
**Вхідні дані:** Короткі або розгорнуті описи датасетів українською чи англійською мовами.
**Результат:** Чисті метадані для каталогізації та автоматичного завантаження.

## 2. Опис полів JSON
| Поле | Тип | Опис |
| :--- | :--- | :--- |
| `dataset_title` | string | Повна офіційна назва набору даних. |
| `data_types` | array[str] | Список типів (напр., `tabular`, `geospatial`, `image`, `text`, `audio`). |
| `record_count` | integer | Загальна кількість записів (рядків). Має бути числом. |
| `file_formats` | array[str] | Доступні формати (напр., `CSV`, `JSON`, `XML`, `Parquet`). |
| `access_level` | string | Рівень доступу (Enum). |
| `license` | string | Тип ліцензії (напр., `CC-0`, `MIT`, `Open Data Commons`). |

## 3. Required Fields (Обов'язкові поля)
Для успішної валідації об'єкт **мусить** містити всі ключі:
* `dataset_title`
* `data_types`
* `record_count`
* `file_formats`
* `access_level`
* `license`

## 4. JSON Schema
""" + json_start + """{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "dataset_title": { "type": "string" },
    "data_types": {
      "type": "array",
      "items": { "type": "string" }
    },
    "record_count": { "type": ["integer", "null"] },
    "file_formats": {
      "type": "array",
      "items": { "type": "string" }
    },
    "access_level": {
      "type": "string",
      "enum": ["public", "upon_request", "commercial"]
    },
    "license": { "type": ["string", "null"] }
  },
  "required": ["dataset_title", "data_types", "record_count", "file_formats", "access_level", "license"]
}
""" + json_end + """
## 5. Правила для null / missing values
* Якщо поле **відсутнє** у тексті (напр., не вказана кількість записів), модель повинна повернути `null`, а не вигадувати число або повертати `0`.
* Порожні масиви `[]` дозволені для `file_formats`, якщо формати не вказані.
* Рядки не можуть бути порожніми `""` — замість них використовується `null`.

## 6. Проблемні поля (Common Issues)
1. **`record_count`**: Найчастіше ламається через спробу моделі повернути текст (напр., `"10к"`) замість числа (`10000`).
2. **`access_level`**: Моделі часто намагаються перекласти значення (напр., `"відкритий"`) замість використання системного ключа `"public"`.
3. **`license`**: Галюцинація ліцензій, які не згадуються в тексті.

## 7. Робота Repair Loop
Механізм виправлення (Repair Loop) у цьому проєкті фокусується на:
* **Примусова нормалізація типів:** Перетворення `"5 млн"` -> `5000000`.
* **Виправлення Enum:** Мапінг значень на дозволений список (`public`, `upon_request`, `commercial`).
* **Додавання відсутніх ключів:** Якщо модель пропустила поле `license`, Repair Loop змушує його додати зі значенням `null`.
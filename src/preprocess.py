import re
import ftfy
from typing import Dict, List, Any

# Патерни для маскування PII
URL_PATTERN = re.compile(r'https?://\S+|www\.\S+|bit\.ly/\S+')
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')

# Патерни для типографіки
QUOTES_PATTERN = re.compile(r'[«»“”„]')
DASHES_PATTERN = re.compile(r'[—–]')
APOSTROPHES_PATTERN = re.compile(r"[`’‘ʼ]")

# Словник українських скорочень, після яких НЕ треба розбивати речення
UA_ABBREVIATIONS = r'(?i)\b(м|вул|просп|пров|бул|буд|кв|р|рр|ім|о|ст|тис|млн|млрд|див|с|смт|обл|т\.д|т\.п)\.'


def fix_encoding(text: str) -> str:
    """Виправляє бите кодування за допомогою ftfy"""
    return ftfy.fix_text(text)

def normalize_typography(text: str) -> str:
    """Уніфікує апострофи, лапки та тире до стандартних машинописних символів"""
    text = APOSTROPHES_PATTERN.sub("'", text)
    text = QUOTES_PATTERN.sub('"', text)
    text = DASHES_PATTERN.sub("-", text)
    return text

def mask_pii(text: str) -> str:
    """Маскує email-адреси та веб-посилання"""
    text = EMAIL_PATTERN.sub('<EMAIL>', text)
    text = URL_PATTERN.sub('<URL>', text)
    return text

def clean_whitespace(text: str) -> str:
    """Видаляє зайві пробіли, табуляції та переноси рядків"""
    return re.sub(r'\s+', ' ', text).strip()

def clean_news_artifacts(text: str) -> str:
    """
    Очищає специфічне сміття для новин
    Наприклад, вступні міста: (Київ) - ..., або кінцеві джерела: Про це повідомляє...
    """
    text = re.sub(r'^\([А-ЯІЇЄҐ][а-яіїєґ]+\)\s*-\s*', '', text)
    return text


def split_sentences(text: str) -> List[str]:
    """
    Розбиває текст на речення, ігноруючи крапки у скороченнях (м., вул.) та числах
    """
    if not text:
        return []

    # Крок 1: Захищаємо скорочення
    # Захищаємо відомі українські абревіатури
    protected_text = re.sub(UA_ABBREVIATIONS, r'\1<DOT>', text)
    
    # Захищаємо крапки в числах та версіях
    protected_text = re.sub(r'(\d)\.(\d)', r'\1<DOT>\2', protected_text)
    
    # Захищаємо ініціали
    protected_text = re.sub(r'\b([А-ЯІЇЄҐA-Z])\.', r'\1<DOT>', protected_text)

    # Крок 2: Розбиваємо текст за маркерами кінця речення (. ! ? або багатокрапка)
    sentences_raw = re.split(r'(?<=[.!?…])\s+(?=[А-ЯІЇЄҐA-Z0-9"«])', protected_text)

    # Крок 3: Повертаємо крапки на місце і чистимо пробіли
    sentences = []
    for s in sentences_raw:
        restored_sentence = s.replace('<DOT>', '.').strip()
        if restored_sentence:
            sentences.append(restored_sentence)

    # Фоллбек: якщо регулярка нічого не розбила
    if not sentences and text:
        return [text]

    return sentences


def preprocess(text: Any) -> Dict[str, Any]:
    """
    Повний детермінований пайплайн препроцесингу тексту.
    Повертає словник з оригінальним текстом, очищеним та списком речень.
    """
    if not isinstance(text, str) or not text.strip():
        return {
            "raw": str(text) if text else "",
            "clean": "",
            "sentences": []
        }

    raw_text = text

    # 1. Виправлення кодування
    clean = fix_encoding(raw_text)
    
    # 2. Видалення новинного сміття
    clean = clean_news_artifacts(clean)
    
    # 3. Нормалізація типографіки
    clean = normalize_typography(clean)
    
    # 4. Табличні артефакти
    clean = clean.replace('|', ' ')
    
    # 5. Видалення дубльованих лапок ("" -> ")
    clean = re.sub(r'""+', '"', clean)
    
    # 6. Видалення технічного Instagram-шуму
    clean = re.sub(r'Посмотреть эту публикацию в Instagram', '', clean, flags=re.IGNORECASE)

    # 7. Маскування PII
    clean = mask_pii(clean)
    
    # 8. Фінальна чистка пробілів
    clean = clean_whitespace(clean)
    
    # 9. Розбиття на речення
    sentences = split_sentences(clean)

    return {
        "raw": raw_text,
        "clean": clean,
        "sentences": sentences
    }

# для локальної перевірки
if __name__ == "__main__":
    test_text = "(Київ) - Компанія «IT-News» повідомляє: у 2024 р. очікується ріст на 15.5%. Пишіть на info@news.ua або заходьте на http://news.ua! Про це заявив В.О. Зеленський у м. Львів."
    
    result = preprocess(test_text)
    
    print("Raw")
    print(result["raw"])
    print("\nClean")
    print(result["clean"])
    print("\nSentences")
    for i, s in enumerate(result["sentences"], 1):
        print(f"{i}: {s}")
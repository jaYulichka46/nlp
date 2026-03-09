import re
import json
import os
from datetime import datetime

def load_agencies_dict():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    dict_path = os.path.join(base_dir, 'resources', 'ua_agencies.json')
    try:
        with open(dict_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️ Словник не знайдено за шляхом: {dict_path}")
        return {}

UA_AGENCIES = load_agencies_dict()

MONTHS_MAP = {
    "січня": "01", "лютого": "02", "березня": "03", "квітня": "04",
    "травня": "05", "червня": "06", "липня": "07", "серпня": "08",
    "вересня": "09", "жовтня": "10", "листопада": "11", "грудня": "12"
}

def extract_money(text: str) -> list:
    results = []
    pattern = r'(?i)(\$|usd|євро|eur)?\s*(\d+(?:[.,]\d+)?)\s*(млн|млрд|тис(?:яч[а-я]*)?|мільйон[а-я]*|мільярд[а-я]*)?(?:\s*(грн|гривен[ь|я]|uah|\$|usd|євро|eur|долар[а-я]*|цент[і|и|ів]))?'
    
    for match in re.finditer(pattern, text):
        currency_prefix = match.group(1)
        num_str = match.group(2).replace(',', '.')
        multiplier_str = match.group(3)
        currency_suffix = match.group(4)
    
        if not currency_prefix and not currency_suffix:
            continue
            
        try:
            amount = float(num_str)

            if multiplier_str:
                mult = multiplier_str.lower()
                if mult.startswith('тис'): amount *= 1_000
                elif mult.startswith('млн') or mult.startswith('мільйон'): amount *= 1_000_000
                elif mult.startswith('млрд') or mult.startswith('мільярд'): amount *= 1_000_000_000
            
            currency = 'UAH'
            full_currency_str = f"{currency_prefix or ''} {currency_suffix or ''}".lower()
            
            if 'usd' in full_currency_str or '$' in full_currency_str or 'долар' in full_currency_str:
                currency = 'USD'
            elif 'eur' in full_currency_str or 'євро' in full_currency_str:
                currency = 'EUR'
                
            results.append({
                "field_type": "MONEY_AMOUNT",
                "value": {"amount": amount, "currency": currency},
                "start_char": match.start(),
                "end_char": match.end(),
                "method": "regex_money"
            })
        except ValueError:
            continue
    return results


def extract_dates(text: str) -> list:
    results = []
    current_year = "2026"
    pattern_digital = r'(?<!\d)(\d{2})\.(\d{2})(?:\.(\d{4}))?(?!\d)'
    for match in re.finditer(pattern_digital, text):
        day, month, year = match.groups()
        if not year: year = current_year
        if 1 <= int(day) <= 31 and 1 <= int(month) <= 12:
            results.append({
                "field_type": "DATE_EVENT",
                "value": f"{day}.{month}.{year}",
                "start_char": match.start(),
                "end_char": match.end(),
                "method": "regex_date_digital"
            })

    months_pattern = '|'.join(MONTHS_MAP.keys())
    pattern_text = rf'(?i)(?<!\d)(\d{{1,2}})\s+({months_pattern})(?:\s+(\d{{4}})(?:-го)?\s*року?)?'
    for match in re.finditer(pattern_text, text):
        day, month_word, year = match.groups()
        if not year: year = current_year
        month = MONTHS_MAP.get(month_word.lower())
        day = day.zfill(2)
        
        results.append({
            "field_type": "DATE_EVENT",
            "value": f"{day}.{month}.{year}",
            "start_char": match.start(),
            "end_char": match.end(),
            "method": "regex_date_text"
        })
            
    return results

def extract_agencies(text: str) -> list:
    results = []
    if not UA_AGENCIES:
        return results
    sorted_keys = sorted(UA_AGENCIES.keys(), key=len, reverse=True)
    escaped_keys = [re.escape(k) for k in sorted_keys]
    pattern = r'(?i)(?<![а-яА-Яіїєґ])(' + '|'.join(escaped_keys) + r')(?![а-яА-Яіїєґ])'
    
    for match in re.finditer(pattern, text):
        raw_val = match.group(1).lower()
        normalized_val = UA_AGENCIES.get(raw_val)
        
        results.append({
            "field_type": "UA_AGENCY",
            "value": normalized_val,
            "start_char": match.start(),
            "end_char": match.end(),
            "method": "dictionary_match"
        })
        
    return results

def extract_all(text: str) -> list:
    if not isinstance(text, str) or not text.strip():
        return []
        
    all_entities = []
    all_entities.extend(extract_money(text))
    all_entities.extend(extract_dates(text))
    all_entities.extend(extract_agencies(text))
    
    all_entities.sort(key=lambda x: x['start_char'])
    return all_entities

if __name__ == "__main__":
    sample = "Кабмін 15 березня 2024 року виділив 1.5 млрд грн, а ЗСУ отримали $50 тисяч. Дедлайн 10.05."
    print("Тестовий текст:", sample)
    print(json.dumps(extract_all(sample), indent=2, ensure_ascii=False))
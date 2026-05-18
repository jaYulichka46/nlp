import re

def extract_key_entities(input_data: dict) -> dict:
    """
    Витягує популярні сутності (локації, організації, політики) з тексту новини.
    Очікуваний input: {"text": "Сьогодні в Києві президент зустрівся з представниками НАТО."}
    """
    try:
        text = input_data.get("text", "")
        if not text:
            raise ValueError("Field 'text' is missing or empty.")
            
        # Спрощений словник сутностей для демонстрації (rule-based)
        entities_db = {
            "locations": ["київ", "харків", "одеса", "львів", "дніпро", "донеччина", "крим", "сша", "єс", "британія"],
            "organizations": ["зсу", "нато", "верховна рада", "кабмін", "мвс", "сбу", "оон", "мвф"],
            "persons": ["зеленський", "сирський", "залужний", "байден", "макрон", "шольц"]
        }

        text_lower = text.lower()
        found_entities = {"locations": [], "organizations": [], "persons": []}
        
        for category, keywords in entities_db.items():
            for kw in keywords:
                if re.search(rf'\b{re.escape(kw)}\b', text_lower):
                    found_entities[category].append(kw.capitalize())

        total_found = sum(len(items) for items in found_entities.values())

        return {
            "entities": found_entities,
            "total_entities_found": total_found
        }
    except Exception as e:
        raise ValueError(f"Entity extraction failed: {str(e)}")

def categorize_news(input_data: dict) -> dict:
    """
    Визначає категорію новини на основі ключових слів.
    Очікуваний input: {"text": "На фронті тривають важкі бої, працює ППО."}
    """
    try:
        text = input_data.get("text", "").lower()
        if not text:
            raise ValueError("Field 'text' is missing or empty.")
            
        categories_keywords = {
            "War/Military": ["зсу", "фронт", "обстріл", "ракета", "дрон", "ппо", "атака", "вибух", "військові"],
            "Politics": ["закон", "президент", "депутат", "парламент", "уряд", "вибори", "санкції"],
            "Economy": ["бюджет", "гривня", "долар", "економіка", "податки", "кредит", "інфляція", "мвф"],
            "Sports": ["матч", "футбол", "олімпіада", "чемпіонат", "збірна", "турнір"]
        }
        
        scores = {cat: 0 for cat in categories_keywords}
        
        for category, keywords in categories_keywords.items():
            for kw in keywords:
                if re.search(rf'\b{re.escape(kw)}\b', text):
                    scores[category] += 1
                    
        # Знаходимо категорію з найбільшим скором
        best_category = max(scores, key=scores.get)
        
        if scores[best_category] == 0:
            return {"category": "General/Unknown", "confidence_score": 0}
            
        return {
            "category": best_category,
            "matched_keywords_count": scores[best_category]
        }
    except Exception as e:
        raise ValueError(f"News categorization failed: {str(e)}")

# Реєстр доступних інструментів
AVAILABLE_TOOLS = {
    "extract_key_entities": extract_key_entities,
    "categorize_news": categorize_news
}
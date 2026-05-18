# Knowledge Base: Read-only resources
NEWS_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {
            "type": "string",
            "enum": ["Politics", "War/Military", "Economy", "Sports", "General"],
            "description": "Головна категорія новини."
        },
        "entities": {
            "type": "object",
            "properties": {
                "locations": {"type": "array", "items": {"type": "string"}},
                "persons": {"type": "array", "items": {"type": "string"}},
                "organizations": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["locations", "persons", "organizations"]
        }
    },
    "required": ["category", "entities"]
}

# Ключові слова для простого роутингу (щоб відсіяти нерелевантне)
WEATHER_KEYWORDS = ["погода", "опади", "температура", "градусів", "вітер", "хмарно"]
SPAM_KEYWORDS = ["шок", "сенсація", "терміново", "переходь за посиланням", "виграй", "казино"]
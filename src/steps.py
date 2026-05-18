import json
import re
from .flow_state import FlowState
from .schemas import WEATHER_KEYWORDS, SPAM_KEYWORDS, NEWS_ANALYSIS_SCHEMA
from jsonschema import validate, ValidationError

def ingest(state: FlowState) -> FlowState:
    """Етап 1: Прийом, очищення та перевірка на порожнечу."""
    if not state.raw_text or not state.raw_text.strip():
        state.status = "failed"
        state.errors.append("Текст новини порожній.")
        return state
        
    state.clean_text = " ".join(state.raw_text.split())
    state.status = "ingested"
    return state

def route(state: FlowState) -> FlowState:
    """Етап 2: Маршрутизація. Відсіюємо погоду та клікбейт."""
    if state.status == "failed": return state
    
    text_lower = state.clean_text.lower()
    
    if any(kw in text_lower for kw in WEATHER_KEYWORDS):
        state.route = "weather_skip"
        state.routing_reason = "Знайдено маркери прогнозу погоди. Аналіз не потрібен."
    elif any(kw in text_lower for kw in SPAM_KEYWORDS):
        state.route = "spam_skip"
        state.routing_reason = "Знайдено маркери клікбейту або спаму."
    else:
        state.route = "news_analysis"
        state.routing_reason = "Релевантний текст новини. Передаємо на аналіз LLM."
        
    state.status = "routed"
    return state

def execute(state: FlowState, llm_caller) -> FlowState:
    """Етап 3: Виклик LLM для структурування новини."""
    if state.status == "failed" or state.route != "news_analysis":
        return state
        
    prompt = f"""
    Проаналізуй цю українську новину. Визнач її категорію та витягни ключові іменовані сутності (локації, особи, організації).
    Відповідь має СУВОРО відповідати такій JSON схемі: {json.dumps(NEWS_ANALYSIS_SCHEMA)}
    Новина: '{state.clean_text}'
    """
    
    try:
        response = llm_caller(prompt)
        cleaned_response = response.replace("```json", "").replace("```", "").strip()
        state.extracted_data = json.loads(cleaned_response)
        state.status = "executed"
    except Exception as e:
        state.status = "execution_error"
        state.errors.append(f"Помилка LLM або JSON-парсингу: {str(e)}")
        
    return state

def validate_step(state: FlowState) -> FlowState:
    """Етап 4: Перевірка JSON-схеми."""
    if state.status in ["failed", "execution_error"] or state.route != "news_analysis":
        return state
        
    try:
        validate(instance=state.extracted_data, schema=NEWS_ANALYSIS_SCHEMA)
        state.validation_result = {"schema_ok": True}
        state.status = "validated"
            
    except ValidationError as e:
        state.validation_result = {"schema_ok": False, "error": e.message}
        state.status = "validation_failed"
        state.errors.append(f"Провал валідації схеми: {e.message}")
        
    return state

def apply_fallback(state: FlowState) -> FlowState:
    """Етап 5: Safe Failure. Якщо LLM впала, пробуємо витягти категорію примітивно."""
    if state.status in ["validation_failed", "execution_error"]:
        state.fallback_triggered = True
        state.warnings.append("LLM збій. Активовано базовий Fallback (категорія за замовчуванням).")
        
        if state.route == "news_analysis":
            # Якщо модель не змогла відповісти JSON-ом, ставимо категорію "General" і пусті масиви
            state.extracted_data = {
                "category": "General",
                "entities": {"locations": [], "persons": [], "organizations": []}
            }
                
        state.status = "recovered_via_fallback"
        
    return state

def export(state: FlowState) -> dict:
    """Етап 6: Формування фінального об'єкта експорту."""
    export_payload = {
        "case_id": state.case_id,
        "route": state.route,
        "final_output": None,
        "needs_manual_review": state.fallback_triggered or bool(state.errors),
        "status": state.status,
        "warnings": state.warnings,
        "errors": state.errors
    }
    
    if state.route == "news_analysis" and state.extracted_data:
        export_payload["final_output"] = state.extracted_data
    elif state.route == "weather_skip":
        export_payload["final_output"] = {"message": "Прогноз погоди. Екстракцію пропущено."}
    elif state.route == "spam_skip":
        export_payload["final_output"] = {"message": "Клікбейт/Спам. Екстракцію пропущено."}
    else:
        export_payload["final_output"] = {"message": "Не вдалося витягти дані."}
        
    state.final_output = export_payload
    return export_payload
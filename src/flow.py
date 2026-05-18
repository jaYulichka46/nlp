from .flow_state import FlowState
from .steps import ingest, route, execute, validate_step, apply_fallback, export
from .flow_logger import log_flow_state

def run_news_flow(raw_text: str, llm_caller, case_id: str = None, log_file: str = "docs/flow_logs_lab14.jsonl") -> dict:
    """
    Запускає stateful пайплайн для аналізу українських новин.
    """
    # Ініціалізація стану
    state = FlowState(raw_text=raw_text, case_id=case_id)
    
    # 1. Ingest & Route
    state = ingest(state)
    state = route(state)
    
    # 2. Execute & Validate (Тільки для цільових новин)
    if state.route == "news_analysis":
        state = execute(state, llm_caller)
        state = validate_step(state)
    
    # 3. Fallback & Export
    state = apply_fallback(state)
    final_result = export(state)
    
    # 4. Логування
    log_flow_state(state, log_file)
    
    return final_result
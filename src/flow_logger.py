import json
import os
from .flow_state import FlowState

def log_flow_state(state: FlowState, log_file="docs/flow_logs_lab14.jsonl"):
    os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else '.', exist_ok=True)
    
    log_entry = {
        "case_id": state.case_id,
        "input": state.raw_text,
        "route": state.route,
        "validation_result": state.validation_result,
        "fallback_triggered": state.fallback_triggered,
        "fallback_result": state.status if state.fallback_triggered else None,
        "export_output": state.final_output,
        "final_status": state.status,
        "errors": state.errors,
        "warnings": state.warnings
    }
    
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
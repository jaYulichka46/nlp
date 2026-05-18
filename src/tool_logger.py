import json
from datetime import datetime
import os

class ToolLogger:
    def __init__(self, log_path="docs/tool_logs_lab12.jsonl"):
        self.log_path = log_path
        # Створюємо директорію, якщо її немає
        os.makedirs(os.path.dirname(self.log_path) if os.path.dirname(self.log_path) else '.', exist_ok=True)

    def log_call(self, task_id, tool_name, tool_input, tool_output, success, error_msg=None):
        """
        Зберігає інформацію про виклик інструменту у JSONL файл.
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "task_id": task_id,
            "tool_name": tool_name,
            "input": tool_input,
            "output": tool_output,
            "success": success,
            "error": error_msg
        }
        
        with open(self.log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
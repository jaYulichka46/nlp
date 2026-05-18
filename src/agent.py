import json
from .tools import AVAILABLE_TOOLS
from .tool_logger import ToolLogger

class ToolGroundedAgent:
    def __init__(self, llm_caller, logger: ToolLogger, max_steps=4):
        self.llm = llm_caller
        self.logger = logger
        self.max_steps = max_steps
        self.tools = AVAILABLE_TOOLS

    def build_system_prompt(self):
        tool_descriptions = """
1. extract_key_entities: Extracts known locations, organizations, and persons from the news text. Input format: {"text": "<news text>"}
2. categorize_news: Classifies the news into a category (e.g., War, Politics, Economy, Sports) based on keywords. Input format: {"text": "<news text>"}
"""
        return f"""
You are a Ukrainian News Analyst Assistant. 
You must analyze the provided news snippet by extracting key entities and determining its category using the provided tools.

Available tools:
{tool_descriptions}

You must respond STRICTLY in JSON format with ONE of these two structures:

OPTION 1: To call a tool
{{
    "thought": "I need to categorize this news first.",
    "tool_name": "categorize_news",
    "tool_input": {{"text": "Сьогодні в Києві ухвалили новий бюджет."}}
}}

OPTION 2: To give the final answer
{{
    "thought": "I have categorized the news and extracted entities.",
    "final_answer": "Ця новина належить до категорії 'Economy'. Знайдені сутності: локація Київ."
}}
"""

    def run(self, task_id: str, user_input: str):
        conversation_history = self.build_system_prompt() + f"\n\nUser Task: Analyze this news snippet: '{user_input}'"
        
        tool_call_count = 0
        
        for step in range(self.max_steps):
            llm_response = self.llm(conversation_history)
            
            try:
                cleaned_response = llm_response.replace("```json", "").replace("```", "").strip()
                agent_action = json.loads(cleaned_response)
            except json.JSONDecodeError:
                conversation_history += f"\n\nSystem Error: Your response was not valid JSON. You MUST return JSON only. Broken response: {llm_response}"
                continue

            if "final_answer" in agent_action:
                return {
                    "task_id": task_id,
                    "tool_calls": tool_call_count,
                    "final_answer": agent_action["final_answer"],
                    "status": "success"
                }
                
            if "tool_name" in agent_action and "tool_input" in agent_action:
                tool_name = agent_action["tool_name"]
                tool_input = agent_action["tool_input"]
                tool_call_count += 1
                
                if tool_name not in self.tools:
                    error_msg = f"Tool '{tool_name}' not found."
                    self.logger.log_call(task_id, tool_name, tool_input, None, False, error_msg)
                    conversation_history += f"\n\nTool Result: Error - {error_msg}"
                    continue
                    
                try:
                    tool_func = self.tools[tool_name]
                    tool_output = tool_func(tool_input)
                    self.logger.log_call(task_id, tool_name, tool_input, tool_output, True)
                    conversation_history += f"\n\nTool Result for '{tool_name}':\n{json.dumps(tool_output)}"
                except Exception as e:
                    self.logger.log_call(task_id, tool_name, tool_input, None, False, str(e))
                    conversation_history += f"\n\nTool Result for '{tool_name}': Error - {str(e)}"
            else:
                conversation_history += "\n\nSystem Error: Missing required fields in JSON."
                
        return {
            "task_id": task_id,
            "tool_calls": tool_call_count,
            "final_answer": "Agent reached maximum steps without a final answer.",
            "status": "timeout"
        }
import uuid

class FlowState:
    def __init__(self, raw_text: str, case_id: str = None):
        # Ingest data
        self.case_id = case_id or f"news_{uuid.uuid4().hex[:8]}"
        self.raw_text = raw_text
        self.clean_text = raw_text.strip()
        
        # Route data
        self.route = None
        self.routing_reason = None
        
        # Execute data
        self.extracted_data = None
        
        # Validation & Fallback
        self.validation_result = {}
        self.fallback_triggered = False
        self.fallback_result = None
        
        # Final output & logs
        self.status = "ingested" 
        self.final_output = None
        self.errors = []
        self.warnings = []

    @property
    def dict(self):
        return {
            "case_id": self.case_id,
            "raw_text": self.raw_text,
            "clean_text": self.clean_text,
            "route": self.route,
            "routing_reason": self.routing_reason,
            "extracted_data": self.extracted_data,
            "validation_result": self.validation_result,
            "fallback_triggered": self.fallback_triggered,
            "status": self.status,
            "errors": self.errors,
            "warnings": self.warnings
        }
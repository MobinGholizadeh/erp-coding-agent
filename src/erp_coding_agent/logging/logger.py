import logging
import json
from datetime import datetime, timezone
from typing import Any

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        # Add any extra attributes from record if they exist
        if hasattr(record, "task_id"):
            log_data["task_id"] = record.task_id
            
        if hasattr(record, "agent_state"):
            log_data["agent_state"] = record.agent_state
            
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

def setup_logger(name: str = "erp_coding_agent", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Prevent duplicate logging
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        
    return logger

# Default logger instance
logger = setup_logger()

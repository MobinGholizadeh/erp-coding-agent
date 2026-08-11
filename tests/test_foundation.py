import pytest
import json
from erp_coding_agent.config.settings import get_settings
from erp_coding_agent.domain.models import Task, Event
from erp_coding_agent.domain.states import TaskStatus
from erp_coding_agent.error_handling.exceptions import AgentException, BuildError
from erp_coding_agent.logging.logger import setup_logger

def test_settings_load_defaults():
    settings = get_settings()
    assert settings.agent.max_attempts == 5
    assert settings.llm.provider == "qwen"
    assert settings.knowledge.timeout_seconds == 30

def test_task_model_creation():
    task = Task(
        task_id="TEST-001",
        instruction="Fix the bug",
        repository="/tmp/repo"
    )
    assert task.status == TaskStatus.IDLE
    assert task.attempt == 0
    assert task.max_attempts == 5
    assert len(task.events) == 0

def test_event_model():
    event = Event(type="TASK_CREATED", details={"info": "started"})
    assert event.type == "TASK_CREATED"
    assert "info" in event.details

def test_exceptions():
    with pytest.raises(AgentException):
        raise BuildError("Compilation failed")

def test_logger_format(capsys):
    import logging
    import io
    
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    from erp_coding_agent.logging.logger import JSONFormatter
    handler.setFormatter(JSONFormatter())
    
    logger = logging.getLogger("test_logger")
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    
    logger.info("Test message", extra={"task_id": "TEST-001", "agent_state": "READY"})
    
    output = stream.getvalue()
    log_dict = json.loads(output)
    
    assert log_dict["message"] == "Test message"
    assert log_dict["task_id"] == "TEST-001"
    assert log_dict["agent_state"] == "READY"
    assert log_dict["level"] == "INFO"

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0"}

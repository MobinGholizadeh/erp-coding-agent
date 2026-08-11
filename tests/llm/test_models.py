import pytest
from erp_coding_agent.llm.models import Message, Role, TokenUsage, LLMRequest, LLMResponse

def test_message_creation():
    msg = Message(role=Role.USER, content="Hello")
    assert msg.role == Role.USER
    assert msg.content == "Hello"

def test_llm_request_creation():
    msg = Message(role=Role.USER, content="Hello")
    req = LLMRequest(messages=[msg], temperature=0.5, model="test-model")
    assert req.temperature == 0.5
    assert req.model == "test-model"
    assert len(req.messages) == 1

def test_llm_response_creation():
    usage = TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    resp = LLMResponse(content="Response", usage=usage, structured_data={"key": "value"})
    assert resp.content == "Response"
    assert resp.usage.total_tokens == 30
    assert resp.structured_data == {"key": "value"}

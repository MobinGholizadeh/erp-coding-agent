import pytest
from erp_coding_agent.llm.client import MockLLM
from erp_coding_agent.llm.models import LLMRequest, Message, Role, LLMResponse

@pytest.fixture
def mock_llm():
    return MockLLM()

@pytest.mark.asyncio
async def test_mock_generate(mock_llm):
    mock_llm.queue_response(LLMResponse(content="First response"))
    mock_llm.queue_response(LLMResponse(content="Second response"))
    
    req = LLMRequest(messages=[Message(role=Role.USER, content="Hello")])
    
    resp1 = await mock_llm.generate(req)
    assert resp1.content == "First response"
    
    resp2 = await mock_llm.generate(req)
    assert resp2.content == "Second response"
    
    # Defaults to a static response when empty
    resp3 = await mock_llm.generate(req)
    assert resp3.content == "Default mock response"

@pytest.mark.asyncio
async def test_mock_generate_stream(mock_llm):
    mock_llm.queue_stream(["Chunk 1", "Chunk 2"])
    
    req = LLMRequest(messages=[Message(role=Role.USER, content="Hello")])
    
    chunks = []
    async for chunk in mock_llm.generate_stream(req):
        chunks.append(chunk)
        
    assert chunks == ["Chunk 1", "Chunk 2"]

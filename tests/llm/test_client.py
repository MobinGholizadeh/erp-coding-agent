import pytest
import httpx
from unittest.mock import patch, MagicMock
from erp_coding_agent.llm.client import QwenClient
from erp_coding_agent.llm.models import LLMRequest, Message, Role, TokenUsage
from erp_coding_agent.config.settings import LLMSettings
from erp_coding_agent.error_handling.exceptions import LLMAPIError, LLMTimeoutError

@pytest.fixture
def settings():
    return LLMSettings(
        provider="qwen",
        base_url="http://test.local/v1",
        model="test-model",
        api_key="test-key",
        timeout_seconds=1,
        max_retries=1
    )

@pytest.fixture
def qwen_client(settings):
    return QwenClient(settings)

@pytest.mark.asyncio
async def test_qwen_generate_success(qwen_client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "Hello back!"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20}
    }
    
    with patch("httpx.AsyncClient.request", return_value=mock_response):
        req = LLMRequest(messages=[Message(role=Role.USER, content="Hello")])
        resp = await qwen_client.generate(req)
        
        assert resp.content == "Hello back!"
        assert resp.usage.total_tokens == 20

@pytest.mark.asyncio
@patch("asyncio.sleep") # mock sleep to speed up test
async def test_qwen_generate_retry_success(mock_sleep, qwen_client):
    # First fails with 500, second succeeds with 200
    mock_fail = MagicMock()
    mock_fail.status_code = 500
    mock_fail.text = "Internal Server Error"
    
    mock_success = MagicMock()
    mock_success.status_code = 200
    mock_success.json.return_value = {
        "choices": [{"message": {"content": "Hello back!"}}],
        "usage": {}
    }
    
    with patch("httpx.AsyncClient.request", side_effect=[mock_fail, mock_success]):
        req = LLMRequest(messages=[Message(role=Role.USER, content="Hello")])
        resp = await qwen_client.generate(req)
        
        assert resp.content == "Hello back!"
        mock_sleep.assert_called_once()

@pytest.mark.asyncio
@patch("asyncio.sleep")
async def test_qwen_generate_max_retries_exceeded(mock_sleep, qwen_client):
    mock_fail = MagicMock()
    mock_fail.status_code = 500
    mock_fail.text = "Internal Server Error"
    
    # max_retries is 1, so it should attempt twice (initial + 1 retry)
    with patch("httpx.AsyncClient.request", return_value=mock_fail):
        req = LLMRequest(messages=[Message(role=Role.USER, content="Hello")])
        with pytest.raises(LLMAPIError):
            await qwen_client.generate(req)

@pytest.mark.asyncio
@patch("asyncio.sleep")
async def test_qwen_generate_timeout(mock_sleep, qwen_client):
    with patch("httpx.AsyncClient.request", side_effect=httpx.TimeoutException("timeout")):
        req = LLMRequest(messages=[Message(role=Role.USER, content="Hello")])
        with pytest.raises(LLMTimeoutError):
            await qwen_client.generate(req)

@pytest.mark.asyncio
async def test_qwen_generate_structured_output(qwen_client):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"key": "value"}'}}],
        "usage": {}
    }
    
    with patch("httpx.AsyncClient.request", return_value=mock_response):
        req = LLMRequest(
            messages=[Message(role=Role.USER, content="Hello")],
            response_format={"type": "json_object"}
        )
        resp = await qwen_client.generate(req)
        
        assert resp.structured_data == {"key": "value"}

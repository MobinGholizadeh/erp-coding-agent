import pytest
from erp_coding_agent.config.settings import LLMSettings
from erp_coding_agent.llm import get_llm_client, MockLLM, QwenClient

def test_get_llm_client_mock():
    settings = LLMSettings(provider="mock")
    client = get_llm_client(settings)
    assert isinstance(client, MockLLM)

def test_get_llm_client_qwen():
    settings = LLMSettings(provider="qwen", base_url="http://custom/v1", model="fine-tuned")
    client = get_llm_client(settings)
    assert isinstance(client, QwenClient)
    assert client.base_url == "http://custom/v1"
    assert client.default_model == "fine-tuned"

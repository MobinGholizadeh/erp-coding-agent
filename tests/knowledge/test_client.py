import pytest
import httpx

from erp_coding_agent.knowledge import (
    KnowledgeClient,
    MockKnowledgeClient,
    KnowledgeAPIError,
    KnowledgeResourceNotFoundError
)

@pytest.mark.asyncio
async def test_mock_client_search_code():
    client = MockKnowledgeClient()
    results = await client.search_code("test_query")
    assert len(results) == 1
    assert results[0].score == 0.95
    assert "mock_function" in results[0].content

@pytest.mark.asyncio
async def test_mock_client_get_context():
    client = MockKnowledgeClient()
    response = await client.get_context("test_query")
    assert "mock_function" in response.context
    assert response.metadata["sources_count"] == 2

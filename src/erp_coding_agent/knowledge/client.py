import httpx
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from .models import SearchResult, SymbolReference, DependencyInfo, ContextResponse
from .exceptions import KnowledgeAPIError, KnowledgeResourceNotFoundError, KnowledgeTimeoutError

class KnowledgeClient:
    """
    HTTP client for communicating with the code-knowledge-indexer service.
    """
    
    def __init__(self, base_url: str = "http://localhost:8001", timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        
    async def _request(self, method: str, endpoint: str, **kwargs) -> Any:
        url = f"{self.base_url}{endpoint}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.request(method, url, **kwargs)
                if response.status_code == 404:
                    raise KnowledgeResourceNotFoundError(f"Resource not found: {endpoint}")
                response.raise_for_status()
                return response.json()
            except httpx.TimeoutException as e:
                raise KnowledgeTimeoutError(f"Request to {url} timed out") from e
            except httpx.HTTPStatusError as e:
                raise KnowledgeAPIError(f"HTTP error: {e.response.status_code} - {e.response.text}") from e
            except httpx.RequestError as e:
                raise KnowledgeAPIError(f"Request failed: {str(e)}") from e

    async def search_code(self, query: str, limit: int = 10) -> List[SearchResult]:
        data = await self._request("GET", "/api/v1/knowledge/search/code", params={"query": query, "limit": limit})
        return [SearchResult(**item) for item in data]

    async def search_docs(self, query: str, limit: int = 10) -> List[SearchResult]:
        data = await self._request("GET", "/api/v1/knowledge/search/docs", params={"query": query, "limit": limit})
        return [SearchResult(**item) for item in data]

    async def find_symbol(self, name: str) -> List[SearchResult]:
        data = await self._request("GET", f"/api/v1/knowledge/symbols/{quote(name)}")
        return [SearchResult(**item) for item in data]

    async def find_references(self, symbol: str) -> List[SymbolReference]:
        data = await self._request("GET", f"/api/v1/knowledge/symbols/{quote(symbol)}/references")
        return [SymbolReference(**item) for item in data]

    async def find_dependencies(self, symbol: str) -> List[DependencyInfo]:
        data = await self._request("GET", f"/api/v1/knowledge/symbols/{quote(symbol)}/dependencies")
        return [DependencyInfo(**item) for item in data]

    async def find_dependents(self, symbol: str) -> List[DependencyInfo]:
        data = await self._request("GET", f"/api/v1/knowledge/symbols/{quote(symbol)}/dependents")
        return [DependencyInfo(**item) for item in data]

    async def get_context(self, query: str) -> ContextResponse:
        data = await self._request("GET", "/api/v1/knowledge/context", params={"query": query})
        return ContextResponse(**data)

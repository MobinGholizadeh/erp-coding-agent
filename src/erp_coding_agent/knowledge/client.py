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

    async def search_code(self, query: str, limit: int = 10, repository_id: Optional[str] = None) -> List[SearchResult]:
        payload = {"query": query, "limit": limit}
        if repository_id:
            payload["repository_id"] = repository_id
        data = await self._request("POST", "/api/v1/search", json=payload)
        return [SearchResult(
            id=item.get("id"),
            content=item.get("content", ""),
            score=item.get("score"),
            metadata={"file": item.get("file"), "type": item.get("type"), "language": item.get("language"), "symbol": item.get("symbol")}
        ) for item in data.get("results", [])]

    async def search_docs(self, query: str, limit: int = 10, repository_id: Optional[str] = None) -> List[SearchResult]:
        payload = {"query": query, "limit": limit}
        if repository_id:
            payload["repository_id"] = repository_id
        data = await self._request("POST", "/api/v1/docs/search", json=payload)
        return [SearchResult(
            id=item.get("id"),
            content=item.get("content", ""),
            score=item.get("score"),
            metadata={"file": item.get("file"), "type": item.get("type")}
        ) for item in data.get("results", [])]

    async def find_symbol(self, name: str, repository_id: Optional[str] = None) -> List[SearchResult]:
        payload = {"query": name, "limit": 10}
        if repository_id:
            payload["repository_id"] = repository_id
        data = await self._request("POST", "/api/v1/symbols/search", json=payload)
        return [SearchResult(
            id=item.get("id"),
            content=item.get("content", ""),
            score=item.get("score"),
            metadata={"file": item.get("file"), "type": item.get("type"), "symbol": item.get("symbol")}
        ) for item in data.get("results", [])]

    async def find_references(self, symbol: str, repository_id: Optional[str] = None) -> List[SymbolReference]:
        payload = {"symbol": symbol, "limit": 50}
        if repository_id:
            payload["repository_id"] = repository_id
        data = await self._request("POST", "/api/v1/references", json=payload)
        return [SymbolReference(**item) for item in data.get("references", [])]

    async def find_dependencies(self, symbol: str, repository_id: Optional[str] = None) -> List[DependencyInfo]:
        payload = {"symbol": symbol}
        if repository_id:
            payload["repository_id"] = repository_id
        data = await self._request("POST", "/api/v1/dependencies", json=payload)
        return [DependencyInfo(
            target=item.get("target", ""),
            target_label=item.get("target_label", ""),
            type=item.get("type", "")
        ) for item in data.get("dependencies", [])]

    async def find_dependents(self, symbol: str, repository_id: Optional[str] = None) -> List[DependencyInfo]:
        payload = {"symbol": symbol}
        if repository_id:
            payload["repository_id"] = repository_id
        data = await self._request("POST", "/api/v1/dependents", json=payload)
        return [DependencyInfo(
            target=item.get("source", ""),
            target_label=item.get("source_label", ""),
            type=item.get("type", "")
        ) for item in data.get("dependents", [])]

    async def get_context(self, query: str, repository_id: Optional[str] = None) -> ContextResponse:
        payload = {"task": query, "limit": 20}
        if repository_id:
            payload["repository_id"] = repository_id
        data = await self._request("POST", "/api/v1/context", json=payload)
        
        # The indexer returns {"query": ..., "results": {...}}
        results = data.get("results", {})
        if isinstance(results, dict):
            context_str = results.get("context", str(results))
        else:
            context_str = str(results)
            
        return ContextResponse(
            context=context_str,
            metadata={"request_id": data.get("request_id"), "repository_id": data.get("repository_id")}
        )

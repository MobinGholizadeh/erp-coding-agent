from typing import List

from .models import SearchResult, SymbolReference, DependencyInfo, ContextResponse

class MockKnowledgeClient:
    """
    Mock implementation of KnowledgeClient for testing without a running indexer.
    """
    
    def __init__(self, base_url: str = "", timeout: float = 0.0):
        self.base_url = base_url
        self.timeout = timeout

    async def search_code(self, query: str, limit: int = 10) -> List[SearchResult]:
        return [
            SearchResult(
                id="mock_code_1",
                content=f"def mock_function():\n    print('Mock code for: {query}')",
                metadata={"file": "mock_file.py", "language": "python"},
                score=0.95
            )
        ]

    async def search_docs(self, query: str, limit: int = 10) -> List[SearchResult]:
        return [
            SearchResult(
                id="mock_doc_1",
                content=f"# Mock Documentation\n\nThis is a mock doc for query: {query}",
                metadata={"file": "README.md", "language": "markdown"},
                score=0.9
            )
        ]

    async def find_symbol(self, name: str) -> List[SearchResult]:
        return [
            SearchResult(
                id="mock_symbol_1",
                content=f"class {name}:\n    pass",
                metadata={"file": "models.py", "type": "class"},
                score=1.0
            )
        ]

    async def find_references(self, symbol: str) -> List[SymbolReference]:
        return [
            SymbolReference(
                source="src/main.py",
                source_label="main",
                type="calls"
            )
        ]

    async def find_dependencies(self, symbol: str) -> List[DependencyInfo]:
        return [
            DependencyInfo(
                target="src/utils.py",
                target_label="helper_func",
                type="uses"
            )
        ]

    async def find_dependents(self, symbol: str) -> List[DependencyInfo]:
        return [
            DependencyInfo(
                target="src/service.py",
                target_label="ServiceClass",
                type="inherits"
            )
        ]

    async def get_context(self, query: str) -> ContextResponse:
        return ContextResponse(
            context=f"Mock context built for query: {query}\n\nContains:\n- mock_function\n- Mock Documentation",
            metadata={"query": query, "sources_count": 2}
        )

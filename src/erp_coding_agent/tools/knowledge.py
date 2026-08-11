from pydantic import BaseModel, Field
from typing import List

from .base import BaseTool, ToolPermission
from ..config.settings import KnowledgeSettings

class SearchCodeInput(BaseModel):
    query: str = Field(description="The semantic or keyword query to search for.")

class SearchCodeOutput(BaseModel):
    results: List[str]

class SearchCodeTool(BaseTool):
    name = "search_code"
    description = "Search the codebase for a semantic query."
    input_schema = SearchCodeInput
    output_schema = SearchCodeOutput
    permissions = [ToolPermission.NETWORK_ACCESS]

    def __init__(self, settings: KnowledgeSettings):
        self.base_url = settings.base_url

    async def execute(self, query: str) -> SearchCodeOutput:
        # Stub implementation pending Ali's indexer
        return SearchCodeOutput(results=[f"Mock result for: {query}"])


class FindSymbolInput(BaseModel):
    symbol: str = Field(description="The name of the class, function, or variable to find.")

class FindSymbolOutput(BaseModel):
    locations: List[str]

class FindSymbolTool(BaseTool):
    name = "find_symbol"
    description = "Find the definition of a specific symbol."
    input_schema = FindSymbolInput
    output_schema = FindSymbolOutput
    permissions = [ToolPermission.NETWORK_ACCESS]

    def __init__(self, settings: KnowledgeSettings):
        self.base_url = settings.base_url

    async def execute(self, symbol: str) -> FindSymbolOutput:
        # Stub implementation pending Ali's indexer
        return FindSymbolOutput(locations=[f"Mock location for: {symbol}"])


class FindReferencesInput(BaseModel):
    symbol: str = Field(description="The name of the symbol to find references for.")

class FindReferencesOutput(BaseModel):
    references: List[str]

class FindReferencesTool(BaseTool):
    name = "find_references"
    description = "Find all references/usages of a specific symbol."
    input_schema = FindReferencesInput
    output_schema = FindReferencesOutput
    permissions = [ToolPermission.NETWORK_ACCESS]

    def __init__(self, settings: KnowledgeSettings):
        self.base_url = settings.base_url

    async def execute(self, symbol: str) -> FindReferencesOutput:
        # Stub implementation pending Ali's indexer
        return FindReferencesOutput(references=[f"Mock reference for: {symbol}"])

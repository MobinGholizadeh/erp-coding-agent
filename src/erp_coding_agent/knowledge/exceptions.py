class KnowledgeAPIError(Exception):
    """Base exception for Knowledge API errors."""
    pass

class KnowledgeResourceNotFoundError(KnowledgeAPIError):
    """Exception raised when a requested resource (like a symbol) is not found."""
    pass

class KnowledgeTimeoutError(KnowledgeAPIError):
    """Exception raised when the Knowledge API request times out."""
    pass

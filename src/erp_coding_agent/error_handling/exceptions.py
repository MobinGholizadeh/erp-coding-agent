class AgentException(Exception):
    """Base exception for all agent-related errors."""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message

class ConfigurationError(AgentException):
    """Raised when there is an issue with the configuration."""
    pass

class KnowledgeAPIError(AgentException):
    """Raised when there is an error interacting with the Knowledge API."""
    pass

class BuildError(AgentException):
    """Raised when a build operation fails unexpectedly."""
    pass

class TestError(AgentException):
    """Raised when a test operation fails unexpectedly."""
    pass

class RecoveryLimitReached(AgentException):
    """Raised when the maximum number of error recovery attempts has been reached."""
    pass

class LLMError(AgentException):
    """Base exception for all LLM-related errors."""
    pass

class LLMAPIError(LLMError):
    """Raised when the LLM API returns an error (e.g., non-200 status code)."""
    pass

class LLMTimeoutError(LLMError):
    """Raised when the LLM request times out."""
    pass

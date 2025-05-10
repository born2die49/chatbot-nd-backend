class LlmError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LlmProviderError(LlmError):
    """Exception raised when there's an error with the LLM provider."""
    pass


class PromptTemplateError(LlmError):
    """Exception raised when there's an error with prompt templates."""
    pass


class RetrievalError(LlmError):
    """Exception raised when there's an error during retrieval."""
    pass
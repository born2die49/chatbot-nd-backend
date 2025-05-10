class VectorStoreError(Exception):
    """Base exception for vector store related errors"""
    pass

class EmbeddingServiceError(Exception):
    """Exception raised for errors in the embedding service"""
    pass

class ProviderNotFoundError(VectorStoreError):
    """Exception raised when a vector store provider is not found"""
    pass

class EmbeddingModelNotFoundError(VectorStoreError):
    """Exception raised when an embedding model is not found"""
    pass
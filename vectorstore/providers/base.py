from abc import ABC, abstractmethod
from typing import List, Any, Dict

class VectorStoreProvider(ABC):
    """Abstract base class for vector store providers."""
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the vector store with configuration."""
        pass
    
    @abstractmethod
    def create_collection(self, collection_name: str) -> str:
        """Create a new collection in the vector store."""
        pass
    
    @abstractmethod
    def add_documents(self, collection_name: str, document_embeddings: List[Dict[str, Any]]) -> List[str]:
        """Add documents with their embeddings to the vector store.
        
        Args:
            collection_name: Name of the collection
            document_embeddings: List of dicts with 'id', 'embedding', and 'metadata'
        
        Returns:
            List of IDs of the added documents
        """
        pass
        
    @abstractmethod
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from the vector store."""
        pass
      
    @abstractmethod
    def get_retriever(self, collection_name: str, embedding_function: Any) -> Any:
        """Get a retriever for a collection.
        
        Args:
            collection_name: Name of the collection
            embedding_function: Embedding function to use for queries
            
        Returns:
            Retriever object for the collection
        """
        pass
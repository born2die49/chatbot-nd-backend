import logging
from typing import List, Any, Dict
import uuid

from langchain_community.vectorstores import Chroma
from chromadb import EphemeralClient, PersistentClient
from chromadb.errors import ChromaError

from .base import VectorStoreProvider
from ..exceptions import VectorStoreError

logger = logging.getLogger(__name__)

class ChromaVectorStoreProvider(VectorStoreProvider):
    """ChromaDB implementation of the VectorStoreProvider."""
    
    def __init__(self):
        self.client = None
        self.persistent = False
        self.vector_stores: Dict[str, Chroma] = {}
    
    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize ChromaDB client with configuration.
        
        Args:
            config: Dict with configuration parameters
        """
        logger.info("Initializing ChromaDB vector store")
        
        try:
            persistence_directory = config.get('persistence_directory')
            
            if persistence_directory:
                logger.info(f"Using persistent ChromaDB client with directory: {persistence_directory}")
                self.client = PersistentClient(path=persistence_directory)
                self.persistent = True
            else:
                logger.info("Using ephemeral ChromaDB client")
                self.client = EphemeralClient()
                self.persistent = False
                
        except ChromaError as e:
            logger.exception(f"ChromaDB initialization failed: {str(e)}")
            raise VectorStoreError(f"ChromaDB error: {str(e)}") from e
        except Exception as e:
            logger.exception(f"Vector store initialization error: {str(e)}")
            raise VectorStoreError(f"Initialization error: {str(e)}") from e
    
    def create_collection(self, collection_name: str) -> str:
        """Create a new collection in ChromaDB.
        
        Args:
            collection_name: Name for the collection
            
        Returns:
            The collection name
        """
        logger.info(f"Creating ChromaDB collection: {collection_name}")
        
        try:
            self.client.create_collection(name=collection_name)
            return collection_name
        except ChromaError as e:
            logger.exception(f"ChromaDB collection creation failed: {str(e)}")
            raise VectorStoreError(f"ChromaDB error: {str(e)}") from e
    
    def add_documents(self, collection_name: str, document_embeddings: List[Dict[str, Any]]) -> List[str]:
        """Add documents with embeddings to ChromaDB.
        
        Args:
            collection_name: Name of the collection
            document_embeddings: List of dicts with 'id', 'embedding', and 'metadata'
            
        Returns:
            List of IDs of the added documents
        """
        logger.info(f"Adding {len(document_embeddings)} documents to ChromaDB collection {collection_name}")
        
        try:
            collection = self.client.get_collection(name=collection_name)
            
            ids = [item['id'] for item in document_embeddings]
            embeddings = [item['embedding'] for item in document_embeddings]
            metadatas = [item['metadata'] for item in document_embeddings]
            documents = [item['metadata'].get('text', '') for item in document_embeddings]
            
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents
            )
            
            return ids
        except ChromaError as e:
            logger.exception(f"ChromaDB add documents failed: {str(e)}")
            raise VectorStoreError(f"ChromaDB error: {str(e)}") from e
    
    def delete_collection(self, collection_name: str) -> bool:
        """Delete a collection from ChromaDB.
        
        Args:
            collection_name: Name of the collection to delete
            
        Returns:
            True if successful
        """
        logger.info(f"Deleting ChromaDB collection: {collection_name}")
        
        try:
            self.client.delete_collection(name=collection_name)
            return True
        except ChromaError as e:
            logger.exception(f"ChromaDB collection deletion failed: {str(e)}")
            raise VectorStoreError(f"ChromaDB error: {str(e)}") from e
          
    def get_retriever(self, collection_name: str, embedding_function: Any) -> Any:
        """Get a retriever for a collection.
        
        Args:
            collection_name: Name of the collection
            embedding_function: Embedding function to use for queries
            
        Returns:
            Retriever object for the collection
        """
        logger.info(f"Getting retriever for collection: {collection_name}")
        
        try:
            # Check if we already have this vector store
            if collection_name in self.vector_stores:
                vector_store = self.vector_stores[collection_name]
            else:
                # Create a new Chroma instance for the collection
                vector_store = Chroma(
                    client=self.client,
                    collection_name=collection_name,
                    embedding_function=embedding_function
                )
                # Cache the vector store
                self.vector_stores[collection_name] = vector_store
                
            # Return the retriever
            return vector_store.as_retriever()
            
        except ChromaError as e:
            logger.exception(f"ChromaDB retriever creation failed: {str(e)}")
            raise VectorStoreError(f"ChromaDB error: {str(e)}") from e
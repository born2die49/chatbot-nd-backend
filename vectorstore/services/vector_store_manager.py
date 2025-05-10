import logging
import uuid
from typing import List, Dict, Any, Optional

from django.db import transaction
from django.contrib.auth import get_user_model
from document.models import Document, DocumentChunk

from ..models import VectorStoreProvider, VectorStoreInstance, Embedding, EmbeddingModel
from ..exceptions import VectorStoreError, ProviderNotFoundError
from ..providers.chroma_service import ChromaVectorStoreProvider
from .embedding_service import EmbeddingService

User = get_user_model()
logger = logging.getLogger(__name__)

class VectorStoreManager:
    """Service for managing vector store instances."""
    
    def __init__(self):
        self.providers = {
            'chroma': ChromaVectorStoreProvider()
        }
        self.embedding_service = EmbeddingService()
    
    def get_provider(self, provider_slug: str):
        """Get a vector store provider by slug."""
        try:
            provider_model = VectorStoreProvider.objects.get(slug=provider_slug, is_active=True)
            
            if provider_slug not in self.providers:
                raise ProviderNotFoundError(f"Provider implementation not found: {provider_slug}")
            
            provider = self.providers[provider_slug]
            provider.initialize(provider_model.config)
            
            return provider, provider_model
        except VectorStoreProvider.DoesNotExist:
            raise ProviderNotFoundError(f"Provider not found or not active: {provider_slug}")
        except Exception as e:
            logger.exception(f"Error getting vector store provider: {str(e)}")
            raise VectorStoreError(f"Provider error: {str(e)}")
    
    @transaction.atomic
    def create_vector_store(
        self, 
        user, 
        name: str, 
        provider_slug: str,
        embedding_model_id: str,
        config: Dict[str, Any] = None
    ) -> VectorStoreInstance:
        """Create a new vector store instance.
        
        Args:
            user: User who owns the vector store
            name: Name for the vector store
            provider_slug: Slug of the provider to use
            embedding_model_id: ID of the embedding model to use
            config: Optional configuration parameters
            
        Returns:
            Created VectorStoreInstance
        """
        logger.info(f"Creating vector store: {name} with provider {provider_slug}")
        
        try:
            provider_impl, provider_model = self.get_provider(provider_slug)
            embedding_model = EmbeddingModel.objects.get(id=embedding_model_id, is_active=True)
            
            # Generate unique collection name
            collection_name = f"collection_{uuid.uuid4().hex}"
            
            # Create collection in vector store
            provider_impl.create_collection(collection_name)
            
            # Create vector store instance in database
            vector_store = VectorStoreInstance.objects.create(
                name=name,
                user=user,
                provider=provider_model,
                embedding_model=embedding_model,
                collection_name=collection_name,
                config=config or {},
                status='ready'
            )
            
            return vector_store
        except Exception as e:
            logger.exception(f"Failed to create vector store: {str(e)}")
            raise VectorStoreError(f"Failed to create vector store: {str(e)}")
    
    @transaction.atomic
    def add_document_to_vector_store(
        self, 
        vector_store_id: str, 
        document_id: str
    ) -> None:
        """Add a document to a vector store.
        
        Args:
            vector_store_id: ID of the vector store
            document_id: ID of the document to add
        """
        logger.info(f"Adding document {document_id} to vector store {vector_store_id}")
        
        try:
            # Get vector store instance and document
            vector_store = VectorStoreInstance.objects.get(id=vector_store_id)
            document = Document.objects.get(id=document_id)
            
            # Update vector store status
            vector_store.status = 'indexing'
            vector_store.save(update_fields=['status'])
            
            # Get provider
            provider_impl, _ = self.get_provider(vector_store.provider.slug)
            
            # Get document chunks
            chunks = DocumentChunk.objects.filter(document=document)
            
            if not chunks.exists():
                raise VectorStoreError(f"No chunks found for document {document_id}")
            
            # Generate embeddings for chunks
            chunk_texts = [chunk.content for chunk in chunks]
            embeddings = self.embedding_service.generate_embeddings(
                chunk_texts, 
                str(vector_store.embedding_model.id)
            )
            
            # Prepare embeddings for vector store
            document_embeddings = []
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                embedding_id = f"{document.id}_{chunk.chunk_index}"
                document_embeddings.append({
                    'id': embedding_id,
                    'embedding': embedding,
                    'metadata': {
                        'document_id': str(document.id),
                        'chunk_id': str(chunk.id),
                        'chunk_index': chunk.chunk_index,
                        'page_number': chunk.page_number,
                        'text': chunk.content
                    }
                })
            
            # Add to vector store
            added_ids = provider_impl.add_documents(
                vector_store.collection_name, 
                document_embeddings
            )
            
            # Store embedding references in database
            embeddings_to_create = []
            for chunk, embedding_id in zip(chunks, added_ids):
                embeddings_to_create.append(Embedding(
                    document_chunk=chunk,
                    vector_store=vector_store,
                    embedding_id=embedding_id
                ))
            
            Embedding.objects.bulk_create(embeddings_to_create)
            
            # Add document to vector store's documents
            vector_store.documents.add(document)
            
            # Update vector store status
            vector_store.status = 'ready'
            vector_store.save(update_fields=['status'])
            
        except Exception as e:
            logger.exception(f"Failed to add document to vector store: {str(e)}")
            
            # Update vector store status to failed
            try:
                vector_store = VectorStoreInstance.objects.get(id=vector_store_id)
                vector_store.status = 'failed'
                vector_store.error_message = str(e)
                vector_store.save(update_fields=['status', 'error_message'])
            except:
                pass
                
            raise VectorStoreError(f"Failed to add document: {str(e)}")
        
    def get_retriever(self, vector_store_id: str) -> Any:
        """Get a retriever for a vector store instance.
        
        Args:
            vector_store_id: ID of the vector store
            
        Returns:
            Retriever object for the vector store
        """
        logger.info(f"Getting retriever for vector store {vector_store_id}")
        
        try:
            vector_store = VectorStoreInstance.objects.get(id=vector_store_id)
            
            if vector_store.status != 'ready':
                raise VectorStoreError(f"Vector store not ready: {vector_store.status}")
            
            # Get provider
            provider_impl, _ = self.get_provider(vector_store.provider.slug)
            
            # Get embedding model
            embedding_model = self.embedding_service.get_embedding_model(
                str(vector_store.embedding_model.id)
            )
            
            # Get retriever from provider
            return provider_impl.get_retriever(
                vector_store.collection_name, 
                embedding_model
            )
            
        except Exception as e:
            logger.exception(f"Failed to get retriever: {str(e)}")
            raise VectorStoreError(f"Failed to get retriever: {str(e)}")
    
    def delete_vector_store(self, vector_store_id: str) -> None:
        """Delete a vector store instance.
        
        Args:
            vector_store_id: ID of the vector store to delete
        """
        logger.info(f"Deleting vector store {vector_store_id}")
        
        try:
            vector_store = VectorStoreInstance.objects.get(id=vector_store_id)
            
            # Get provider
            provider_impl, _ = self.get_provider(vector_store.provider.slug)
            
            # Delete collection in vector store
            provider_impl.delete_collection(vector_store.collection_name)
            
            # Delete vector store instance from database
            vector_store.delete()
            
        except Exception as e:
            logger.exception(f"Failed to delete vector store: {str(e)}")
            raise VectorStoreError(f"Failed to delete vector store: {str(e)}")
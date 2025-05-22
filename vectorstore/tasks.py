import logging
from celery import shared_task
from .exceptions import VectorStoreError

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, name="vectorstore.tasks.embed_document")
def embed_document(self, vector_store_id, document_id):
    """Celery task to embed document chunks and add them to a vector store.
    
    Args:
        vector_store_id: ID of the vector store
        document_id: ID of the document to process
    """
    from .services.vector_store_manager import VectorStoreManager
    
    logger.info(f"Starting embedding task for document {document_id} in vector store {vector_store_id}")
    
    try:
        manager = VectorStoreManager()
        manager.add_document_to_vector_store(vector_store_id, document_id)
        logger.info(f"Successfully embedded document {document_id}")
    except Exception as e:
        logger.exception(f"Failed to embed document {document_id}: {str(e)}")
        
        # Retry with exponential backoff
        retry_countdown = 60 * (2 ** self.request.retries)  # 60s, 120s, 240s
        self.retry(exc=e, countdown=retry_countdown)

@shared_task(name="vectorstore.tasks.create_vector_store")
def create_vector_store(user_id, name, provider_slug, embedding_model_id, config=None):
    """Celery task to create a new vector store.
    
    Args:
        user_id: ID of the user who owns the vector store
        name: Name for the vector store
        provider_slug: Slug of the provider to use
        embedding_model_id: ID of the embedding model to use
        config: Optional configuration parameters
        
    Returns:
        ID of the created vector store
    """
    from django.contrib.auth import get_user_model
    from .services.vector_store_manager import VectorStoreManager
    
    User = get_user_model()
    
    logger.info(f"Creating vector store '{name}' for user {user_id}")
    
    try:
        user = User.objects.get(id=user_id)
        manager = VectorStoreManager()
        vector_store = manager.create_vector_store(
            user=user,
            name=name,
            provider_slug=provider_slug,
            embedding_model_id=embedding_model_id,
            config=config or {}
        )
        
        logger.info(f"Successfully created vector store {vector_store.id}")
        return str(vector_store.id)
        
    except Exception as e:
        logger.exception(f"Failed to create vector store: {str(e)}")
        raise
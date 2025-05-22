import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from document.models import Document
from .models import VectorStoreInstance

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Document)
def add_document_to_default_vector_store(sender, instance, **kwargs):
    """Signal handler to add a document to the default vector store when its status changes to 'completed'."""
    
    # Only process documents that have completed processing
    if instance.status == 'completed':
        logger.info(f"Document {instance.id} completed processing, adding to vector store")
        
        def queue_embedding_task():
            from .tasks import embed_document
            
            try:
                # Get default vector store for user
                vector_store = VectorStoreInstance.objects.filter(
                    user=instance.user, 
                    status='ready'
                ).first()
                
                if vector_store:
                    logger.info(f"Queueing embedding task for document {instance.id} in vector store {vector_store.id}")
                    # Queue Celery task
                    embed_document.delay(str(vector_store.id), str(instance.id))
                else:
                    logger.warning(f"No active vector store found for user {instance.user.id}, skipping embedding")
            except Exception as e:
                logger.exception(f"Error queueing document for embedding: {str(e)}")
        
        # Use on_commit to ensure database transaction is complete before queueing task
        transaction.on_commit(queue_embedding_task)
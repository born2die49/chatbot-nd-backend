import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from vectorstore.services.vector_store_manager import VectorStoreManager
from vectorstore.tasks import embed_document
from document.models import Document
from .models import EmbeddingModel, VectorStoreInstance, VectorStoreProvider

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Document)
def add_document_to_default_vector_store(sender, instance, **kwargs):
    """
    Signal handler to add a document to the default vector store when its status changes to 'completed'.
    If no default vector store exists for the user, one will be created.
    """
    # Check if the status is 'completed'
    # 'created' argument is False if it's an update, True if it's a new record.
    # We care about the status field update to 'completed'.
    if instance.status == 'completed':
        logger.info(f"Document {instance.id} processing completed. Attempting to add to a vector store for user {instance.user.id}.")

        # Defer the execution until after the current database transaction commits.
        # This ensures that the document instance (and its status) is fully saved.
        def queue_embedding_task_on_commit():
            try:
                # Try to find an existing 'ready' vector store for the user
                vector_store = VectorStoreInstance.objects.filter(
                    user=instance.user,
                    status='ready'
                ).order_by('-created_at').first() # Get the most recent ready one

                if not vector_store:
                    logger.info(f"No ready vector store found for user {instance.user.id}. Attempting to create a default one.")
                    
                    # Fetch the first active provider and embedding model to create a default store
                    # These should be pre-configured in your database (e.g., via Admin or migrations)
                    default_provider = VectorStoreProvider.objects.filter(is_active=True).first()
                    default_embedding = EmbeddingModel.objects.filter(is_active=True).first()

                    if not default_provider:
                        logger.error("CRITICAL: No active VectorStoreProvider found. Cannot create default vector store.")
                        return
                    if not default_embedding:
                        logger.error("CRITICAL: No active EmbeddingModel found. Cannot create default vector store.")
                        return

                    manager = VectorStoreManager()
                    try:
                        vector_store = manager.create_vector_store(
                            user=instance.user,
                            name=f"Default Store - {instance.user.email}", # Or some other unique name logic
                            provider_slug=default_provider.slug,
                            embedding_model_id=str(default_embedding.id)
                        )
                        logger.info(f"Successfully created new default vector store {vector_store.id} for user {instance.user.id}.")
                    except Exception as e_create:
                        logger.error(f"Failed to create default vector store for user {instance.user.id}: {e_create}")
                        # If creation fails, we can't proceed with embedding for this document now.
                        return
                
                # If we have a vector_store (either found or newly created and now 'ready' from create_vector_store)
                if vector_store and vector_store.status == 'ready':
                    logger.info(f"Queueing embedding task for document {instance.id} into vector store {vector_store.id}.")
                    # embed_document is a Celery task
                    embed_document.delay(str(vector_store.id), str(instance.id))
                elif vector_store:
                    logger.warning(f"Vector store {vector_store.id} found/created but is not ready (status: {vector_store.status}). Skipping embedding for doc {instance.id}.")
                else:
                    # This path should ideally not be hit if creation logic is robust.
                    logger.error(f"Could not find or create a suitable vector store for user {instance.user.id}. Document {instance.id} will not be embedded at this time.")

            except Exception as e:
                logger.exception(f"Error in add_document_to_default_vector_store signal for document {instance.id}: {str(e)}")
        
        transaction.on_commit(queue_embedding_task_on_commit)
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction

from document.models import Document

logger = logging.getLogger(__name__)

# Add signals here as needed
# For example, you might want to automatically process documents when they're marked as completed

@receiver(post_save, sender=Document)
def add_document_to_default_vector_store(sender, instance, created, **kwargs):
    """Signal handler to add a document to the default vector store when its status is 'completed'."""
    # This is just a placeholder. In a real application, you would implement this
    # based on your specific requirements, for example:
    
    # if instance.status == 'completed':
    #     def process_document():
    #         from .services.vector_store_manager import VectorStoreManager
    #         try:
    #             # Get default vector store for user
    #             vector_store = VectorStoreInstance.objects.filter(
    #                 user=instance.user, 
    #                 status='ready'
    #             ).first()
    #             
    #             if vector_store:
    #                 manager = VectorStoreManager()
    #                 manager.add_document_to_vector_store(str(vector_store.id), str(instance.id))
    #         except Exception as e:
    #             logger.exception(f"Error adding document to vector store: {str(e)}")
    #     
    #     transaction.on_commit(process_document)
    
    pass
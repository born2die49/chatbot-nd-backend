import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db import transaction
from django.core.exceptions import ObjectDoesNotExist

from .models import Document

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Document)
def process_document_on_create(sender, instance, created, **kwargs):
    """Signal handler to initiate document processing after creation."""
    if created:
        logger.info(f"Triggering processing for newly created document: {instance.id}")
        
        # Process document in background
        # In a real-world application, you would use Celery or similar
        # For simplicity, we're using transaction.on_commit
        def start_processing():
            from .services.document_processing_service import DocumentProcessingService
            try:
                DocumentProcessingService.process_document(instance.id)
            except Exception as e:
                logger.exception(f"Error in document processing task: {str(e)}")
        
        transaction.on_commit(start_processing)
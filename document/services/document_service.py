import logging
import os
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.utils import timezone

from ..models import Document, DocumentChunk, ProcessingStatus
from ..utils.pdf_extractor import PDFExtractor, InvalidFileFormatError, DocumentExtractionError

logger = logging.getLogger(__name__)

class DocumentService:
    """Service for handling document operations."""
    
    @staticmethod
    def create_document(user, file, title=None) -> Document:
        """Create a new document record from an uploaded file.
        
        Args:
            user: User who uploaded the document
            file: Uploaded file object
            title: Optional title for the document (defaults to filename)
            
        Returns:
            Created Document instance
        """
        logger.info(f"Creating document record for file: {file.name}")
        
        # Use filename as title if not provided
        if not title:
            title = os.path.splitext(file.name)[0]
        
        # Get file details
        file_name = file.name
        file_type = file.content_type
        file_size = file.size
        
        # Create document with pending status
        document = Document.objects.create(
            user=user,
            title=title,
            file=file,
            file_name=file_name,
            file_type=file_type,
            file_size=file_size,
            status='pending'
        )
        
        # Create processing status record
        ProcessingStatus.objects.create(document=document)
        
        logger.info(f"Created document record with ID: {document.id}")
        return document
    
    @staticmethod
    def get_document(document_id, user=None) -> Optional[Document]:
        """Get a document by ID, optionally filtered by user.
        
        Args:
            document_id: UUID of the document
            user: Optional user to filter by ownership
            
        Returns:
            Document instance or None if not found
        """
        query = Document.objects.filter(id=document_id)
        if user:
            query = query.filter(user=user)
        
        return query.first()
    
    @staticmethod
    def get_user_documents(user):
        """Get all documents owned by a user.
        
        Args:
            user: User whose documents to retrieve
            
        Returns:
            QuerySet of Document instances
        """
        return Document.objects.filter(user=user).order_by('-created_at')
    
    @staticmethod
    def update_document_status(document, status, error_message=None):
        """Update the processing status of a document.
        
        Args:
            document: Document instance to update
            status: New status value
            error_message: Optional error message
        """
        document.status = status
        if error_message:
            document.error_message = error_message
        document.save(update_fields=['status', 'error_message', 'updated_at'])
        
        # If completed or failed, update processing status end time
        if status in ('completed', 'failed'):
            processing_status = document.processing_status
            processing_status.end_time = timezone.now()
            processing_status.save(update_fields=['end_time'])
            
        logger.info(f"Updated document {document.id} status to: {status}")
    
    @staticmethod
    def delete_document(document):
        """Delete a document and its associated data.
        
        Args:
            document: Document instance to delete
        """
        logger.info(f"Deleting document: {document.id}")
        
        # Delete the file from storage
        if document.file:
            try:
                document.file.delete(save=False)
            except Exception as e:
                logger.warning(f"Error deleting file for document {document.id}: {str(e)}")
        
        # Delete the document record (will cascade to chunks and processing status)
        document.delete()
        
        logger.info(f"Document {document.id} deleted successfully")
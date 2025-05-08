import logging
from typing import List, Dict, Any, Optional
from django.db import transaction
from django.utils import timezone

from ..models import Document, DocumentChunk, ProcessingStatus
from ..utils.pdf_extractor import PDFExtractor, InvalidFileFormatError, DocumentExtractionError
from ..utils.text_cleaner import TextCleaner

logger = logging.getLogger(__name__)

class DocumentProcessingService:
    """Service for processing documents and extracting their content."""
    
    @staticmethod
    def process_document(document_id):
        """Process a document after upload.
        
        This method coordinates the document processing pipeline:
        1. Extract text from the document
        2. Split text into chunks
        3. Store chunks in the database
        
        Args:
            document_id: UUID of the document to process
        """
        from document_service import DocumentService
        
        logger.info(f"Starting processing for document: {document_id}")
        
        # Get the document
        try:
            document = Document.objects.select_related('processing_status').get(id=document_id)
        except Document.DoesNotExist:
            logger.error(f"Document not found: {document_id}")
            return
        
        # Update status to processing
        DocumentService.update_document_status(document, 'processing')
        
        try:
            # Extract text from document
            extracted_pages = DocumentProcessingService._extract_document_text(document)
            
            # Update processing status
            processing_status = document.processing_status
            processing_status.extraction_completed = True
            processing_status.total_pages = len(extracted_pages)
            processing_status.save(update_fields=['extraction_completed', 'total_pages'])
            
            # Process and split text into chunks
            document_chunks = DocumentProcessingService._process_text_chunks(document, extracted_pages)
            
            # Update processing status
            processing_status.chunking_completed = True
            processing_status.processed_pages = len(extracted_pages)
            processing_status.save(update_fields=['chunking_completed', 'processed_pages'])
            
            # Mark document as completed
            DocumentService.update_document_status(document, 'completed')
            
            # Note: Embedding and indexing would be handled separately
            
            logger.info(f"Document processing completed successfully: {document_id}")
            
        except Exception as e:
            logger.exception(f"Error processing document {document_id}: {str(e)}")
            DocumentService.update_document_status(document, 'failed', str(e))
    
    @staticmethod
    def _extract_document_text(document) -> List[Dict[str, Any]]:
        """Extract text from document file.
        
        Args:
            document: Document instance
            
        Returns:
            List of dictionaries containing page content and metadata
        """
        logger.info(f"Extracting text from document: {document.file_name}")
        
        # Read file content
        document.file.open('rb')
        file_content = document.file.read()
        document.file.close()
        
        # Extract text using PDFExtractor
        extracted_pages = PDFExtractor.extract_from_bytes(file_content, document.file_name)
        
        logger.info(f"Extracted {len(extracted_pages)} pages from document {document.id}")
        return extracted_pages
    
    @staticmethod
    def _process_text_chunks(document, extracted_pages) -> List[DocumentChunk]:
        """Process extracted text and create document chunks.
        
        Args:
            document: Document instance
            extracted_pages: List of dictionaries with page content and metadata
            
        Returns:
            List of created DocumentChunk instances
        """
        logger.info(f"Processing text chunks for document: {document.id}")
        
        # Process and split text into chunks
        processed_chunks = TextCleaner.process_text(extracted_pages)
        
        # Create document chunks in database
        with transaction.atomic():
            chunks = []
            for chunk_data in processed_chunks:
                chunk = DocumentChunk(
                    document=document,
                    content=chunk_data['page_content'],
                    chunk_index=chunk_data['metadata'].get('chunk_index', 0),
                    page_number=chunk_data['metadata'].get('page', None)
                )
                chunks.append(chunk)
            
            # Bulk create chunks
            created_chunks = DocumentChunk.objects.bulk_create(chunks)
            
        logger.info(f"Created {len(created_chunks)} chunks for document {document.id}")
        return created_chunks
from django.db import models
from django.contrib.auth import get_user_model
import uuid
import os

User = get_user_model()

def document_upload_path(instance, filename):
    """Generate a unique path for uploaded documents"""
    ext = os.path.splitext(filename)[1]
    unique_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join('documents', unique_filename)

class Document(models.Model):
    """Model representing an uploaded document"""
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to=document_upload_path)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    status = models.CharField(max_length=20, choices=PROCESSING_STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title

class DocumentChunk(models.Model):
    """Model representing a chunk of text extracted from a document"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='chunks')
    content = models.TextField()
    chunk_index = models.IntegerField()
    page_number = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['document', 'chunk_index']
        
    def __str__(self):
        return f"{self.document.title} - Chunk {self.chunk_index}"

class ProcessingStatus(models.Model):
    """Model tracking the processing status of a document"""
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='processing_status')
    extraction_completed = models.BooleanField(default=False)
    chunking_completed = models.BooleanField(default=False)
    embedding_completed = models.BooleanField(default=False)
    indexing_completed = models.BooleanField(default=False)
    total_pages = models.IntegerField(default=0)
    processed_pages = models.IntegerField(default=0)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Processing status for {self.document.title}"
    
    @property
    def is_completed(self):
        return (self.extraction_completed and 
                self.chunking_completed and 
                self.embedding_completed and 
                self.indexing_completed)
    
    @property
    def progress_percentage(self):
        if self.total_pages == 0:
            return 0
        return min(100, int((self.processed_pages / self.total_pages) * 100))
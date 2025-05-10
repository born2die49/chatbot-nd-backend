from django.db import models
from django.contrib.auth import get_user_model
import uuid
from document.models import Document

User = get_user_model()

class VectorStoreProvider(models.Model):
    """Model representing a vector store provider type"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class EmbeddingModel(models.Model):
    """Model representing an embedding model"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    provider = models.CharField(max_length=100)  # e.g., "huggingface", "openai"
    model_id = models.CharField(max_length=255)  # e.g., "all-MiniLM-L6-v2"
    dimension = models.IntegerField()
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.provider})"

class VectorStoreInstance(models.Model):
    """Model representing a vector store instance for documents"""
    STATUS_CHOICES = [
        ('created', 'Created'),
        ('indexing', 'Indexing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vector_stores')
    provider = models.ForeignKey(VectorStoreProvider, on_delete=models.CASCADE, related_name='instances')
    embedding_model = models.ForeignKey(EmbeddingModel, on_delete=models.CASCADE, related_name='vector_stores')
    documents = models.ManyToManyField(Document, related_name='vector_stores')
    collection_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='created')
    error_message = models.TextField(blank=True, null=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Embedding(models.Model):
    """Model representing an embedding of a document chunk"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document_chunk = models.ForeignKey('document.DocumentChunk', on_delete=models.CASCADE, related_name='embeddings')
    vector_store = models.ForeignKey(VectorStoreInstance, on_delete=models.CASCADE, related_name='embeddings')
    embedding_id = models.CharField(max_length=255)  # ID in the vector store
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('document_chunk', 'vector_store')
    
    def __str__(self):
        return f"Embedding for {self.document_chunk}"
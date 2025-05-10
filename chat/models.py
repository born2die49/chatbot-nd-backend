from django.db import models
import uuid
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatSession(models.Model):
    """
    Represents a conversation session between a user and the AI.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_sessions')
    title = models.CharField(max_length=255, default="New Chat")
    vector_store = models.ForeignKey(
        'vectorstore.VectorStoreInstance',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_sessions'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class ChatMessage(models.Model):
    """
    Represents a single message in a chat session.
    """
    MESSAGE_TYPE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=10, choices=MESSAGE_TYPE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional references to sources used for RAG responses
    references = models.JSONField(null=True, blank=True)
    
    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."
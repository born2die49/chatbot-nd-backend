import uuid
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class LlmProvider(models.Model):
    """Model representing an LLM provider (e.g., Groq, OpenAI)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class LlmModel(models.Model):
    """Model representing a specific LLM (e.g., gemma2-9b-it)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    provider = models.ForeignKey(LlmProvider, on_delete=models.CASCADE, related_name='models')
    model_id = models.CharField(max_length=255)  # The actual model ID used by the provider
    is_active = models.BooleanField(default=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.provider.name})"


class PromptTemplate(models.Model):
    """Model for storing reusable prompt templates."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    template = models.TextField()
    template_type = models.CharField(max_length=50, choices=[
        ('qa', 'Question Answering'),
        ('contextualize', 'Contextualizing Questions'),
        ('summarize', 'Summarization'),
        ('custom', 'Custom')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
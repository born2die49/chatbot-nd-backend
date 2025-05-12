from rest_framework import serializers
from vectorstore.models import VectorStoreProvider, EmbeddingModel, VectorStoreInstance
from document.models import Document


class VectorStoreProviderSerializer(serializers.ModelSerializer):
    """
    Serializer for VectorStoreProvider model.
    Used for listing available vector store providers.
    """
    class Meta:
        model = VectorStoreProvider
        fields = ['id', 'name', 'slug']


class EmbeddingModelSerializer(serializers.ModelSerializer):
    """
    Serializer for EmbeddingModel model.
    Used for listing available embedding models.
    """
    class Meta:
        model = EmbeddingModel
        fields = ['id', 'name', 'provider', 'model_id', 'dimension']


class VectorStoreInstanceSerializer(serializers.ModelSerializer):
    """
    Serializer for VectorStoreInstance model.
    Used for list/retrieve operations.
    """
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    embedding_model_name = serializers.CharField(source='embedding_model.name', read_only=True)
    document_count = serializers.SerializerMethodField()
    
    class Meta:
        model = VectorStoreInstance
        fields = ['id', 'name', 'provider', 'provider_name', 'embedding_model', 
                  'embedding_model_name', 'status', 'document_count']
        read_only_fields = ['id', 'provider', 'embedding_model', 'status']
    
    def get_document_count(self, obj):
        """Get the count of documents associated with this vector store instance."""
        return obj.documents.count()


class VectorStoreInstanceCreateSerializer(serializers.Serializer):
    """
    Serializer for creating a new VectorStoreInstance.
    """
    name = serializers.CharField(max_length=255)
    provider_slug = serializers.CharField(max_length=100)
    embedding_model_id = serializers.UUIDField()
    
    def validate_provider_slug(self, value):
        """Validate that the provider slug exists."""
        try:
            VectorStoreProvider.objects.get(slug=value)
            return value
        except VectorStoreProvider.DoesNotExist:
            raise serializers.ValidationError(f"Vector store provider with slug '{value}' does not exist.")
    
    def validate_embedding_model_id(self, value):
        """Validate that the embedding model ID exists."""
        try:
            EmbeddingModel.objects.get(id=value)
            return value
        except EmbeddingModel.DoesNotExist:
            raise serializers.ValidationError(f"Embedding model with ID '{value}' does not exist.")


class AddDocumentToVectorStoreSerializer(serializers.Serializer):
    """
    Serializer for adding a document to a vector store instance.
    """
    document_id = serializers.UUIDField()
    
    def validate_document_id(self, value):
        """Validate that the document ID exists and belongs to the current user."""
        user = self.context['request'].user
        
        try:
            document = Document.objects.get(id=value, user=user)
            return value
        except Document.DoesNotExist:
            raise serializers.ValidationError(
                f"Document with ID '{value}' does not exist or does not belong to you."
            )
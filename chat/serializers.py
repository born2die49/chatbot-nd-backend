from rest_framework import serializers

from vectorstore.models import VectorStoreInstance
from .models import ChatSession, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for chat messages.
    """
    class Meta:
        model = ChatMessage
        fields = ['id', 'message_type', 'content', 'created_at', 'references']
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for chat sessions.
    """
    last_message = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'vector_store', 'is_active', 'created_at', 'updated_at', 'last_message', 'message_count']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_last_message(self, obj):
        """Get the last message in the session."""
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return {
                'content': last_message.content[:100],
                'message_type': last_message.message_type,
                'created_at': last_message.created_at
            }
        return None
    
    def get_message_count(self, obj):
        """Get the total number of messages in the session."""
        return obj.messages.count()


class ChatSessionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new chat sessions.
    """
    class Meta:
        model = ChatSession
        fields = ['title', 'vector_store']
        
    def create(self, validated_data):
        # Get the current user from the request
        user = self.context['request'].user
        
        # Create the chat session
        chat_session = ChatSession.objects.create(
            user=user,
            title=validated_data.get('title', 'New Chat'),
            vector_store=validated_data.get('vector_store', None)
        )
        
        # Add a welcome message
        ChatMessage.objects.create(
            session=chat_session,
            message_type='system',
            content="How can I help you today?"
        )
        
        return chat_session


class MessageCreateSerializer(serializers.Serializer):
    """
    Serializer for creating new messages.
    """
    content = serializers.CharField(required=True)
    
    def validate_content(self, value):
        """Ensure content is not empty."""
        if not value.strip():
            raise serializers.ValidationError("Message content cannot be empty.")
        return value
    
    
class ChatSessionUpdateSerializer(serializers.ModelSerializer):
    # This field expects the UUID of the vector store.
    vector_store = serializers.PrimaryKeyRelatedField(
        queryset=VectorStoreInstance.objects.all(), # Base queryset for validation
        required=False,
        allow_null=True
    )

    class Meta:
        model = ChatSession
        fields = ['title', 'vector_store'] # 'vector_store' refers to the ForeignKey

    def validate_vector_store(self, value):
        # 'value' here is a VectorStoreInstance object if found by PrimaryKeyRelatedField, or None.
        if value is None:
            return None # Allowing dissociation

        user = self.context['request'].user
        if value.user != user:
            raise serializers.ValidationError("You do not have permission to use this vector store.")
        if value.status != 'ready':
            # Allow linking even if indexing, but frontend should be aware.
            # For a stricter approach, uncomment:
            # raise serializers.ValidationError(f"Vector store '{value.name}' is not ready (status: {value.status}).")
            pass
        return value
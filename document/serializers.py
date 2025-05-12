from rest_framework import serializers
from .models import Document, DocumentChunk, ProcessingStatus

class ProcessingStatusSerializer(serializers.ModelSerializer):
    """Serializer for document processing status."""
    
    progress_percentage = serializers.IntegerField(read_only=True)
    is_completed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = ProcessingStatus
        fields = [
            'extraction_completed', 'chunking_completed',
            'embedding_completed', 'indexing_completed',
            'total_pages', 'processed_pages', 
            'start_time', 'end_time',
            'progress_percentage', 'is_completed'
        ]
        read_only_fields = fields

class DocumentChunkSerializer(serializers.ModelSerializer):
    """Serializer for document chunks."""
    
    class Meta:
        model = DocumentChunk
        fields = ['id', 'content', 'chunk_index', 'page_number', 'created_at']
        read_only_fields = fields

class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for documents."""
    
    processing_status = ProcessingStatusSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'file', 'file_url', 'file_name', 'file_type', 'file_size',
            'status', 'error_message', 'created_at', 'updated_at', 'processing_status'
        ]
        read_only_fields = ['id', 'file_url', 'file_name', 'file_type', 'file_size', 
                           'status', 'error_message', 'created_at', 'updated_at']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None

class DocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating documents."""
    
    file = serializers.FileField(required=True)
    title = serializers.CharField(required=False)
    
    class Meta:
        model = Document
        fields = ['title', 'file']
    
    def validate_file(self, value):
        """Validate that the uploaded file is a PDF."""
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError("Only PDF files are supported")
        return value
    
    def create(self, validated_data):
        """Create a new document using DocumentService."""
        from services.document_service import DocumentService
        
        user = self.context['request'].user
        file = validated_data.get('file')
        title = validated_data.get('title')
        
        return DocumentService.create_document(user, file, title)
    
class DocumentListSerializer(serializers.Serializer):
    """
    Serializer for the document list response.
    Extends the existing DocumentSerializer to add pagination and other metadata.
    """
    count = serializers.IntegerField()
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = DocumentSerializer(many=True)
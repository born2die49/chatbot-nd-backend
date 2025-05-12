from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound

from document.models import Document, DocumentChunk
from document.serializers import (
    DocumentCreateSerializer,
    DocumentSerializer,
    DocumentChunkSerializer
)
from document.services import DocumentService


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination settings for document lists."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class DocumentViewSet(viewsets.ModelViewSet):
    """
    API endpoints for Documents:
    
    * GET /documents/ - List user's documents (paginated)
    * POST /documents/ - Upload and create new document
    * GET /documents/{id}/ - Retrieve specific document
    * DELETE /documents/{id}/ - Delete specific document
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        """
        Return different serializers for different actions.
        """
        if self.action == 'create':
            return DocumentCreateSerializer
        return DocumentSerializer
    
    def get_queryset(self):
        """
        Return only documents owned by the authenticated user.
        """
        return Document.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """
        Set the authenticated user as the document owner when creating.
        """
        # Note: DocumentCreateSerializer already sets request.user
        # This is just a safeguard
        serializer.save(user=self.request.user)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a document using the DocumentService.
        """
        instance = self.get_object()
        DocumentService.delete_document(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentChunkViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for DocumentChunks:
    
    * GET /documents/{document_id}/chunks/ - List chunks for a document (paginated)
    * GET /documents/{document_id}/chunks/{id}/ - Retrieve specific chunk
    """
    serializer_class = DocumentChunkSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_document(self):
        """
        Get the document for this request and verify ownership.
        """
        document_id = self.kwargs.get('document_id')
        try:
            return Document.objects.get(id=document_id, user=self.request.user)
        except Document.DoesNotExist:
            raise NotFound(f"Document with ID {document_id} not found or not owned by you.")
    
    def get_queryset(self):
        """
        Return only chunks for the specified document if owned by authenticated user.
        """
        document = self.get_document()
        return DocumentChunk.objects.filter(document=document).order_by('chunk_index')
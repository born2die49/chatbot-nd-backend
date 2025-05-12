from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from vectorstore.models import VectorStoreProvider, EmbeddingModel, VectorStoreInstance
from vectorstore.services.vector_store_manager import VectorStoreManager
from vectorstore.serializers import (
    VectorStoreProviderSerializer,
    EmbeddingModelSerializer,
    VectorStoreInstanceSerializer,
    VectorStoreInstanceCreateSerializer,
    AddDocumentToVectorStoreSerializer
)

# Assume this task exists or will be created
from vectorstore.tasks import embed_document_chunks_for_instance_task


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination settings for vector store instance lists."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class VectorStoreProviderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for VectorStoreProviders:
    
    * GET /vectorstores/providers/ - List all available vector store providers
    * GET /vectorstores/providers/{id}/ - Retrieve specific provider details
    """
    queryset = VectorStoreProvider.objects.all()
    serializer_class = VectorStoreProviderSerializer
    permission_classes = [permissions.IsAuthenticated]


class EmbeddingModelViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for EmbeddingModels:
    
    * GET /vectorstores/embedding-models/ - List all available embedding models
    * GET /vectorstores/embedding-models/{id}/ - Retrieve specific model details
    """
    queryset = EmbeddingModel.objects.all()
    serializer_class = EmbeddingModelSerializer
    permission_classes = [permissions.IsAuthenticated]


class VectorStoreInstanceViewSet(viewsets.ModelViewSet):
    """
    API endpoints for VectorStoreInstances:
    
    * GET /vectorstores/instances/ - List user's vector store instances (paginated)
    * POST /vectorstores/instances/ - Create new vector store instance
    * GET /vectorstores/instances/{id}/ - Retrieve specific instance
    * DELETE /vectorstores/instances/{id}/ - Delete specific instance
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        """
        Return different serializers for different actions.
        """
        if self.action == 'create':
            return VectorStoreInstanceCreateSerializer
        return VectorStoreInstanceSerializer
    
    def get_queryset(self):
        """
        Return only vector store instances owned by the authenticated user.
        """
        return VectorStoreInstance.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """
        Create a new vector store instance using the VectorStoreManager service.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Use service to create vector store instance
        vector_store = VectorStoreManager.create_vector_store(
            user=request.user,
            name=serializer.validated_data['name'],
            provider_slug=serializer.validated_data['provider_slug'],
            embedding_model_id=serializer.validated_data['embedding_model_id']
        )
        
        # Return the created instance using the detail serializer
        response_serializer = VectorStoreInstanceSerializer(vector_store)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a vector store instance using the VectorStoreManager service.
        """
        instance = self.get_object()
        VectorStoreManager.delete_vector_store(instance.id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class AddDocumentToVectorStoreView(generics.CreateAPIView):
    """
    API endpoint to add a document to a vector store instance:
    
    * POST /vectorstores/instances/{instance_id}/documents/ - Add document to vector store
    """
    serializer_class = AddDocumentToVectorStoreSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_vector_store_instance(self):
        """
        Get the vector store instance and verify ownership.
        """
        instance_id = self.kwargs.get('instance_id')
        try:
            return VectorStoreInstance.objects.get(id=instance_id, user=self.request.user)
        except VectorStoreInstance.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound(f"Vector store instance with ID {instance_id} not found or not owned by you.")
    
    def create(self, request, *args, **kwargs):
        """
        Add a document to the vector store instance and start async embedding process.
        """
        vector_store_instance = self.get_vector_store_instance()
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document_id = serializer.validated_data['document_id']
        
        # Use service to add document to vector store
        VectorStoreManager.add_document_to_vector_store(
            vector_store_id=vector_store_instance.id,
            document_id=document_id
        )
        
        # Start async task for embedding
        embed_document_chunks_for_instance_task.delay(
            instance_id=str(vector_store_instance.id), 
            document_id=str(document_id)
        )
        
        return Response(
            {"status": "Processing started", "message": "Document is being processed and embedded."},
            status=status.HTTP_202_ACCEPTED
        )
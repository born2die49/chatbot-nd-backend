from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views.chat_views import ChatSessionViewSet, ChatMessageViewSet
from api.views.document_views import DocumentViewSet, DocumentChunkViewSet
from api.views.user_views import UserProfileView
from api.views.vectorstore_views import (
  VectorStoreProviderViewSet,
  EmbeddingModelViewSet,
  VectorStoreInstanceViewSet,
  AddDocumentToVectorStoreView                  
)

# Create routers for ViewSets
router = DefaultRouter()
router.register(r'documents', DocumentViewSet, basename='document')
router.register(r'vectorstores/providers', VectorStoreProviderViewSet, basename='vectorstore-provider')
router.register(r'vectorstores/embedding-models', EmbeddingModelViewSet, basename='embedding-model')
router.register(r'vectorstores/instances', VectorStoreInstanceViewSet, basename='vectorstore-instance')
router.register(r'chat/sessions', ChatSessionViewSet, basename='chat-session')

# API v1 URL patterns
urlpatterns = [
    # User profile endpoint
    path('profile/', UserProfileView.as_view(), name='user-profile'),
    
    # Include router URLs
    path('', include(router.urls)),
    
    # Nested endpoints for document chunks
    path('documents/<uuid:document_id>/chunks/', 
         DocumentChunkViewSet.as_view({'get': 'list'}), 
         name='document-chunk-list'),
    path('documents/<uuid:document_id>/chunks/<uuid:pk>/', 
         DocumentChunkViewSet.as_view({'get': 'retrieve'}), 
         name='document-chunk-detail'),
    
    # Endpoint to add documents to vector store
    path('vectorstores/instances/<uuid:instance_id>/documents/', 
         AddDocumentToVectorStoreView.as_view(), 
         name='vectorstore-instance-add-document'),
         
    # Chat message endpoints nested under chat sessions
    path('chat/sessions/<uuid:session_id>/messages/',
         ChatMessageViewSet.as_view({'get': 'list', 'post': 'create'}),
         name='chat-message-list'),
]
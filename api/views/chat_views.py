from rest_framework import viewsets, permissions, status, generics
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import NotFound

from chat.models import ChatSession, ChatMessage
from chat.serializers import (
    ChatSessionSerializer, 
    ChatMessageSerializer,
    ChatSessionCreateSerializer, 
    MessageCreateSerializer
)
from chat.services import ChatService
from chat.tasks import process_user_message, generate_session_title
from chat.serializers import ChatSessionUpdateSerializer


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination settings for chat session and message lists."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class ChatSessionViewSet(viewsets.ModelViewSet):
    """
    API endpoints for ChatSessions:
    
    * GET /chat/sessions/ - List user's chat sessions (paginated)
    * POST /chat/sessions/ - Create new chat session
    * GET /chat/sessions/{id}/ - Retrieve specific session
    * PUT/PATCH /chat/sessions/{id}/ - Update session (e.g., title)
    * DELETE /chat/sessions/{id}/ - Delete specific session
    """
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        """
        Return different serializers for different actions.
        """
        if self.action == 'create':
            return ChatSessionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return ChatSessionUpdateSerializer
        return ChatSessionSerializer
    
    def get_queryset(self):
        """
        Return only chat sessions owned by the authenticated user.
        """
        return ChatSession.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """
        Create a new chat session using the ChatService.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Extract data
        title = serializer.validated_data.get('title', 'New Chat')
        vector_store_id = serializer.validated_data.get('vector_store')
        
        # Use service to create session
        session = ChatService.create_session(
            user=request.user,
            title=title,
            vector_store_id=vector_store_id
        )
        
        # If title was not provided or is default, generate a title asynchronously
        if title == 'New Chat':
            generate_session_title.delay(str(session.id), str(request.user.id))
        
        # Return the created session
        response_serializer = ChatSessionSerializer(session)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        """
        Update chat session (currently only title).
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Update the session title using the service
        if 'title' in serializer.validated_data:
            ChatService.update_session_title(
                session_id=instance.id,
                user=request.user,
                title=serializer.validated_data['title']
            )
        
        # Re-fetch the instance to get updated data
        instance = self.get_object()
        response_serializer = ChatSessionSerializer(instance)
        return Response(response_serializer.data)
    
    def destroy(self, request, *args, **kwargs):
        """
        Delete a chat session using the ChatService.
        """
        instance = self.get_object()
        ChatService.delete_session(session_id=instance.id, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ChatMessageViewSet(viewsets.ModelViewSet):
    """
    API endpoints for ChatMessages within a session:
    
    * GET /chat/sessions/{session_id}/messages/ - List messages in session
    * POST /chat/sessions/{session_id}/messages/ - Create new user message
    """
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    http_method_names = ['get', 'post', 'head', 'options']  # Limit to GET, POST only
    
    def get_chat_session(self):
        """
        Get the chat session for this request and verify ownership.
        """
        session_id = self.kwargs.get('session_id')
        try:
            return ChatSession.objects.get(id=session_id, user=self.request.user)
        except ChatSession.DoesNotExist:
            raise NotFound(f"Chat session with ID {session_id} not found or not owned by you.")
    
    def get_queryset(self):
        """
        Return only messages for the specified session if owned by authenticated user.
        """
        session = self.get_chat_session()
        # Order by created_at to get chronological order of messages
        return ChatMessage.objects.filter(session=session).order_by('created_at')
    
    def get_serializer_class(self):
        """
        Return different serializers for different actions.
        """
        if self.action == 'create':
            return MessageCreateSerializer
        return ChatMessageSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new user message and trigger processing.
        """
        session = self.get_chat_session()
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        content = serializer.validated_data['content']
        
        # Add user message to the session
        message = ChatService.add_user_message(
            session_id=session.id,
            user=request.user,
            content=content
        )
        
        # Trigger async processing of the message
        process_user_message.delay(
            session_id=str(session.id),
            user_id=str(request.user.id),
            content=content
        )
        
        # Return the created message
        response_serializer = ChatMessageSerializer(message)
        return Response(
            {
                "message": response_serializer.data,
                "status": "Processing started",
                "info": "Assistant response will be generated asynchronously."
            },
            status=status.HTTP_202_ACCEPTED
        )
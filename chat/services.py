from typing import List, Dict, Optional, Any
import uuid
import logging
from django.db import transaction
from django.contrib.auth import get_user_model

from .models import ChatSession, ChatMessage
from vectorstore.services.vector_store_manager import VectorStoreManager
from llm.tasks import process_retrieval_query, generate_direct_response

logger = logging.getLogger(__name__)

User = get_user_model()

class ChatService:
    """
    Service for managing chat sessions and messages.
    """
    
    @staticmethod
    def create_session(user: Any, title: str = "New Chat", vector_store_id: Optional[str] = None) -> ChatSession:
        """
        Create a new chat session for a user.
        """
        with transaction.atomic():
            session = ChatSession.objects.create(
                user=user,
                title=title,
                vector_store_id=vector_store_id
            )
            
            # Add a system welcome message
            ChatMessage.objects.create(
                session=session,
                message_type='system',
                content="How can I help you today?"
            )
            
            return session
    
    @staticmethod
    def get_session(session_id: str, user: Any) -> Optional[ChatSession]:
        """
        Retrieve a specific chat session for a user.
        """
        try:
            return ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            return None
    
    @staticmethod
    def get_user_sessions(user: Any) -> List[ChatSession]:
        """
        Get all chat sessions for a user.
        """
        return ChatSession.objects.filter(user=user, is_active=True)
    
    @staticmethod
    def delete_session(session_id: str, user: Any) -> bool:
        """
        Delete (soft delete) a chat session.
        """
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
            session.is_active = False
            session.save()
            return True
        except ChatSession.DoesNotExist:
            return False
    
    @staticmethod
    def update_session_title(session_id: str, user: Any, title: str) -> Optional[ChatSession]:
        """
        Update the title of a chat session.
        """
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
            session.title = title
            session.save()
            return session
        except ChatSession.DoesNotExist:
            return None
    
    @staticmethod
    def add_user_message(session_id: str, user: Any, content: str) -> Optional[ChatMessage]:
        """
        Add a user message to a chat session.
        """
        logger.info(f"Attempting to add user message. Session ID: {session_id}, User: {user}, User Authenticated: {user.is_authenticated if hasattr(user, 'is_authenticated') else 'N/A'}")
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
            logger.info(f"Found session: {session.id}, owned by: {session.user}")
            
            if session.user != user:
                logger.warning(f"User mismatch: Request user {user} (ID: {user.id if hasattr(user,'id') else 'N/A'}) does not match session owner {session.user} (ID: {session.user.id if hasattr(session.user,'id') else 'N/A'}) for session {session_id}.")
                return None
            
            message = ChatMessage.objects.create(
                session=session,
                message_type='user',
                content=content
            )
            logger.info(f"User message created with ID: {message.id}")
            return message
        except ChatSession.DoesNotExist:
            logger.error(f"ChatSession with ID {session_id} not found.")
            raise  
    
    @staticmethod
    def add_assistant_message(session_id: str, content: str, references: Optional[Dict] = None) -> ChatMessage:
        """
        Add an assistant message to a chat session.
        """
        session = ChatSession.objects.get(id=session_id)
        message = ChatMessage.objects.create(
            session=session,
            message_type='assistant',
            content=content,
            references=references
        )
        return message
    
    @staticmethod
    def get_chat_history(session_id: str, user: Any) -> List[ChatMessage]:
        """
        Get the message history for a chat session.
        """
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
            return ChatMessage.objects.filter(session=session)
        except ChatSession.DoesNotExist:
            return []
    
    @staticmethod
    def format_chat_history(messages: List[ChatMessage]) -> List[Dict[str, str]]:
        """
        Format chat messages into a list of dictionaries suitable for the LLM.
        """
        formatted_messages = []
        
        for message in messages:
            if message.message_type == 'system':
                continue
                
            role = "user" if message.message_type == 'user' else "assistant"
            formatted_messages.append({
                "role": role,
                "content": message.content
            })
            
        return formatted_messages
    
    @staticmethod
    def process_message(session_id: str, user: Any, content: str) -> Dict[str, Any]:
        """
        Process a user message, generate a response, and save both to the chat history.
        This is the main method that orchestrates the RAG process.
        """
        # Get the chat session
        session = ChatService.get_session(session_id, user)
        if not session:
            return {"status": "error", "message": "Chat session not found"}
        
        # Add the user message to chat history
        user_message = ChatService.add_user_message(session_id, user, content)
        if not user_message:
            return {"status": "error", "message": "Failed to add user message"}
        
        # Get the chat history
        messages = ChatMessage.objects.filter(session=session)
        chat_history = ChatService.format_chat_history(messages)
        
        # Generate assistant response
        if session.vector_store_id:
            # RAG-based response if vector store is associated
            response_dict = process_retrieval_query(
                question=content,
                vector_store_id=str(session.vector_store_id),
                chat_history=chat_history,
                user_id=str(user.id)
            )
            
            if response_dict.get("status") == "success":
                answer = response_dict.get("answer", "")
                # Extract references if available
                references = response_dict.get("references", None)
                
                # Add the assistant message
                assistant_message = ChatService.add_assistant_message(
                    session_id=session_id, 
                    content=answer,
                    references=references
                )
                
                return {
                    "status": "success",
                    "message_id": str(assistant_message.id),
                    "content": answer,
                    "references": references
                }
            else:
                error_msg = response_dict.get("error", "Unknown error occurred")
                # Add error as assistant message
                assistant_message = ChatService.add_assistant_message(
                    session_id=session_id,
                    content=f"I'm sorry, I encountered an error: {error_msg}"
                )
                return {
                    "status": "error",
                    "message": error_msg,
                    "message_id": str(assistant_message.id)
                }
        else:
            # Direct LLM response if no vector store is associated
            response_dict = generate_direct_response(
                prompt=content,
                chat_history=chat_history
            )
            
            if response_dict.get("status") == "success":
                answer = response_dict.get("response", "")
                assistant_message = ChatService.add_assistant_message(
                    session_id=session_id,
                    content=answer
                )
                return {
                    "status": "success",
                    "message_id": str(assistant_message.id),
                    "content": answer
                }
            else:
                error_msg = response_dict.get("error", "Unknown error occurred")
                assistant_message = ChatService.add_assistant_message(
                    session_id=session_id,
                    content=f"I'm sorry, I encountered an error: {error_msg}"
                )
                return {
                    "status": "error",
                    "message": error_msg,
                    "message_id": str(assistant_message.id)
                }
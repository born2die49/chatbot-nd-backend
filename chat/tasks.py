from typing import Dict, Any, Optional
import logging

# Uncomment when Celery is configured
# from celery import shared_task

from .services import ChatService
from llm.tasks import process_retrieval_query, generate_direct_response

logger = logging.getLogger(__name__)

# @shared_task
def process_user_message(session_id: str, user_id: str, content: str) -> Dict[str, Any]:
    """
    Process a user message asynchronously.
    This task is responsible for:
    1. Saving the user message
    2. Getting a response from the LLM (RAG or direct)
    3. Saving the assistant response
    4. Returning the result
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        return ChatService.process_message(session_id, user, content)
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to process message: {str(e)}"
        }

# @shared_task
def generate_session_title(session_id: str, user_id: str) -> Dict[str, Any]:
    """
    Generate a title for a chat session based on its first messages.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        session = ChatService.get_session(session_id, user)
        
        if not session:
            return {"status": "error", "message": "Session not found"}
        
        # Get the first user message
        messages = ChatService.get_chat_history(session_id, user)
        first_msg = next((m for m in messages if m.message_type == 'user'), None)
        
        if not first_msg:
            return {"status": "success", "title": "New Chat"}  # Keep default if no messages
        
        # Generate title using LLM
        prompt = f"Generate a very short title (3-5 words) for a conversation that starts with: '{first_msg.content}'. Return only the title text."
        
        response = generate_direct_response(prompt=prompt)
        
        if response.get("status") == "success":
            title = response.get("response", "").strip()
            title = title[:255]  # Truncate to fit CharField max_length
            
            # Update session title
            updated_session = ChatService.update_session_title(session_id, user, title)
            if updated_session:
                return {"status": "success", "title": title}
        
        return {"status": "error", "message": "Failed to generate title"}
    
    except Exception as e:
        logger.error(f"Error generating session title: {str(e)}")
        return {
            "status": "error",
            "message": f"Failed to generate title: {str(e)}"
        }
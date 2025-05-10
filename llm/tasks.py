import logging
from typing import Dict, List, Optional

# If you have Celery configured
# from celery import shared_task

from .services import LlmService, RetrieverService
from .exceptions import LlmError

logger = logging.getLogger(__name__)

# If using Celery, uncomment the decorator
# @shared_task
def process_retrieval_query(
    question: str, 
    vector_store_id: str, 
    chat_history: Optional[List] = None,
    user_id: Optional[str] = None
) -> Dict:
    """
    Process a query using retrieval-augmented generation.
    
    Args:
        question: The user's question
        vector_store_id: ID of the vector store to query
        chat_history: Optional chat history for context
        user_id: Optional user ID for tracking/permissions
        
    Returns:
        Dict with answer and metadata
    """
    try:
        # This would be imported here to avoid circular imports
        from vectorstore.services.vector_store_manager import VectorStoreManager
        
        # Get the retriever for the specified vector store
        vector_store_manager = VectorStoreManager()
        retriever = vector_store_manager.get_retriever(vector_store_id)
        
        # Get answer using the retriever
        llm_service = LlmService()
        retriever_service = RetrieverService(llm_service)
        answer = retriever_service.get_answer_with_sources(question, retriever, chat_history)
        
        return {
            "answer": answer,
            "status": "success"
        }
        
    except Exception as e:
        logger.exception(f"Error processing retrieval query: {e}")
        return {
            "answer": "I'm sorry, I couldn't process your request at this time.",
            "status": "error",
            "error": str(e)
        }

# If using Celery, uncomment the decorator
# @shared_task
def generate_direct_response(
    prompt: str,
    chat_history: Optional[List] = None,
    model_id: Optional[str] = None
) -> Dict:
    """
    Generate a direct response from the LLM without retrieval.
    
    Args:
        prompt: The user's input
        chat_history: Optional chat history
        model_id: Optional specific model to use
        
    Returns:
        Dict with response and metadata
    """
    try:
        llm_service = LlmService(model_id=model_id)
        retriever_service = RetrieverService(llm_service)
        response = retriever_service.generate_direct_response(prompt, chat_history)
        
        return {
            "response": response,
            "status": "success"
        }
    
    except Exception as e:
        logger.exception(f"Error generating direct response: {e}")
        return {
            "response": "I'm sorry, I couldn't generate a response at this time.",
            "status": "error",
            "error": str(e)
        }
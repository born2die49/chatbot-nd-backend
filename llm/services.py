import logging
from typing import Any, Dict, List, Optional
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_groq import ChatGroq
from django.conf import settings

from .models import LlmProvider, LlmModel, PromptTemplate
from .exceptions import LlmProviderError, PromptTemplateError, RetrievalError
from .prompts import PromptTemplateManager

logger = logging.getLogger(__name__)


class LlmService:
    """Service for interacting with language models."""
    
    def __init__(self, provider_slug=None, model_id=None):
        """Initialize LLM service with optional provider and model."""
        self.provider_slug = provider_slug
        self.model_id = model_id
        self.llm = None
        self.prompt_manager = PromptTemplateManager()
    
    def get_llm(self):
        """Get or initialize an LLM instance."""
        if self.llm:
            return self.llm
            
        try:
            if not self.provider_slug:
                # Use default provider from settings or get the first active one
                provider = LlmProvider.objects.filter(is_active=True).first()
                if not provider:
                    raise LlmProviderError("No active LLM provider found")
                self.provider_slug = provider.slug
            else:
                provider = LlmProvider.objects.get(slug=self.provider_slug, is_active=True)
            
            if not self.model_id:
                # Get the first active model for this provider
                model = LlmModel.objects.filter(provider=provider, is_active=True).first()
                if not model:
                    raise LlmProviderError(f"No active models found for provider {provider.name}")
                self.model_id = model.model_id
            else:
                model = LlmModel.objects.get(provider=provider, model_id=self.model_id, is_active=True)
            
            # Initialize the LLM based on provider
            if provider.slug == 'groq':
                api_key = provider.config.get('api_key', settings.GROQ_API_KEY)
                self.llm = ChatGroq(
                    groq_api_key=api_key,
                    model=model.model_id
                )
            else:
                # Placeholder for other providers
                raise LlmProviderError(f"Provider {provider.name} not supported")
                
            return self.llm
            
        except LlmProvider.DoesNotExist:
            raise LlmProviderError(f"LLM provider {self.provider_slug} not found or not active")
        except LlmModel.DoesNotExist:
            raise LlmProviderError(f"LLM model {self.model_id} not found or not active")
        except Exception as e:
            logger.exception(f"Failed to initialize LLM: {str(e)}")
            raise LlmProviderError(f"Failed to initialize LLM: {str(e)}")


class RetrieverService:
    """Service for handling retrieval-based operations with LLMs."""
    
    def __init__(self, llm_service=None):
        """Initialize retriever service with optional LLM service."""
        self.llm_service = llm_service or LlmService()
        self.prompt_manager = PromptTemplateManager()
    
    def get_answer_with_sources(self, question: str, retriever: Any, chat_history: List = None) -> str:
        """Generate an answer using the retriever and LLM."""
        try:
            # Ensure we have an LLM instance
            llm = self.llm_service.get_llm()
            
            # Convert chat history to the format expected by LangChain if provided
            if chat_history is None:
                chat_history = []
            
            # Create context-aware question based on chat history
            contextualize_q_prompt = self.prompt_manager.create_contextualize_q_prompt()
            history_aware_retriever = create_history_aware_retriever(
                llm, retriever, contextualize_q_prompt
            )
            
            # Create the QA prompt
            qa_prompt = self.prompt_manager.create_qa_prompt()
            
            # Create the QA chain
            qa_chain = create_stuff_documents_chain(llm, qa_prompt)
            
            # Create the retrieval chain
            retrieval_chain = create_retrieval_chain(
                history_aware_retriever, qa_chain
            )
            
            # Run the chain
            response = retrieval_chain.invoke({
                "input": question,
                "chat_history": chat_history
            })
            
            return response["answer"]
            
        except Exception as e:
            logger.exception(f"Failed to generate answer: {str(e)}")
            raise RetrievalError(f"Failed to generate answer: {str(e)}")
    
    def generate_direct_response(self, prompt: str, chat_history: List = None) -> str:
        """Generate a direct response from the LLM without retrieval."""
        try:
            # Ensure we have an LLM instance
            llm = self.llm_service.get_llm()
            
            # Simple direct invocation without retrieval
            if chat_history is None:
                response = llm.invoke(prompt)
            else:
                # Format chat history into messages
                messages = []
                for entry in chat_history:
                    if isinstance(entry, dict):
                        messages.append(entry)
                    else:
                        # Assume tuple of (human_message, ai_message)
                        messages.append({"role": "user", "content": entry[0]})
                        messages.append({"role": "assistant", "content": entry[1]})
                
                # Add the current prompt
                messages.append({"role": "user", "content": prompt})
                response = llm.invoke(messages)
            
            return response.content
            
        except Exception as e:
            logger.exception(f"Failed to generate direct response: {str(e)}")
            raise LlmProviderError(f"Failed to generate response: {str(e)}")
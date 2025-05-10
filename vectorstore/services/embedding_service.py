import logging
from typing import List, Dict, Any, Optional

from django.conf import settings
from langchain_huggingface import HuggingFaceEmbeddings

from ..models import EmbeddingModel
from ..exceptions import EmbeddingServiceError, EmbeddingModelNotFoundError

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Service for generating embeddings from text."""
    
    def __init__(self):
        self.embedding_models = {}
    
    def get_embedding_model(self, model_id: str) -> Any:
        """Get an embedding model by ID.
        
        Args:
            model_id: ID of the embedding model
            
        Returns:
            Initialized embedding model instance
        """
        try:
            # Check if model is already initialized
            if model_id in self.embedding_models:
                logger.debug(f"Using cached embedding model: {model_id}")
                return self.embedding_models[model_id]
            
            # Get model from database
            try:
                model = EmbeddingModel.objects.get(id=model_id)
            except EmbeddingModel.DoesNotExist:
                raise EmbeddingModelNotFoundError(f"Embedding model not found: {model_id}")
            
            # Initialize model based on provider
            if model.provider == 'huggingface':
                logger.info(f"Initializing HuggingFace embedding model: {model.model_id}")
                embedding_model = HuggingFaceEmbeddings(model_name=model.model_id)
                self.embedding_models[model_id] = embedding_model
                return embedding_model
            else:
                raise EmbeddingServiceError(f"Unsupported embedding provider: {model.provider}")
                
        except Exception as e:
            logger.exception(f"Failed to initialize embedding model: {str(e)}")
            raise EmbeddingServiceError(f"Embedding model initialization failed: {str(e)}")
    
    def generate_embeddings(self, texts: List[str], model_id: str) -> List[List[float]]:
        """Generate embeddings for a list of texts.
        
        Args:
            texts: List of text strings to embed
            model_id: ID of the embedding model to use
            
        Returns:
            List of embedding vectors
        """
        logger.info(f"Generating embeddings for {len(texts)} texts using model {model_id}")
        
        try:
            embedding_model = self.get_embedding_model(model_id)
            embeddings = embedding_model.embed_documents(texts)
            return embeddings
        except Exception as e:
            logger.exception(f"Embedding generation failed: {str(e)}")
            raise EmbeddingServiceError(f"Embedding generation failed: {str(e)}")
    
    def generate_embedding(self, text: str, model_id: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            model_id: ID of the embedding model to use
            
        Returns:
            Embedding vector
        """
        logger.debug(f"Generating embedding for single text using model {model_id}")
        
        try:
            embedding_model = self.get_embedding_model(model_id)
            embedding = embedding_model.embed_query(text)
            return embedding
        except Exception as e:
            logger.exception(f"Embedding generation failed: {str(e)}")
            raise EmbeddingServiceError(f"Embedding generation failed: {str(e)}")
    
    @staticmethod
    def get_default_embedding_model() -> Optional[EmbeddingModel]:
        """Get the default embedding model.
        
        Returns:
            Default EmbeddingModel or None if not found
        """
        try:
            return EmbeddingModel.objects.filter(is_active=True).first()
        except Exception as e:
            logger.exception(f"Failed to get default embedding model: {str(e)}")
            return None
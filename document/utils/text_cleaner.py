import re
import logging
from typing import List, Dict, Any, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class TextCleaner:
    """Utility class for cleaning and processing text from documents."""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean document text by removing noise and standardizing format.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned text
        """
        logger.debug("Cleaning document text")
        
        # Replace newlines with spaces
        text = re.sub(r'[\n\r]+', ' ', text)
        
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove page footer indicators
        text = re.sub(r'page \d+ of \d+', '', text, flags=re.IGNORECASE)
        
        # Fix common OCR errors (optional, can be expanded)
        text = text.replace('l/', 'i/')
        text = text.replace('|', 'I')
        
        return text.strip()
    
    @staticmethod
    def calculate_avg_text_length(documents: List[Dict[str, Any]]) -> float:
        """Calculate average length of text in a collection of documents.
        
        Args:
            documents: List of document dictionaries with 'page_content' key
            
        Returns:
            Average text length as float
        """
        if not documents:
            return 0
            
        total_length = sum(len(doc["page_content"]) for doc in documents)
        return total_length / len(documents)
    
    @staticmethod
    def determine_chunk_parameters(avg_text_length: float) -> Tuple[int, int]:
        """Determine optimal chunk size and overlap based on average text length.
        
        Args:
            avg_text_length: Average length of text in documents
            
        Returns:
            Tuple of (chunk_size, chunk_overlap)
        """
        if avg_text_length > 1000:
            logger.debug(f"Long documents detected. Using smaller chunk size.")
            return 500, 50  # Smaller chunks for long docs
        
        logger.debug(f"Shorter documents detected. Using larger chunk size.")
        return 1500, 200  # Larger chunks for shorter docs
    
    @staticmethod
    def split_documents(
        documents: List[Dict[str, Any]], 
        chunk_size: int = 1000, 
        chunk_overlap: int = 100
    ) -> List[Dict[str, Any]]:
        """Split documents into smaller chunks for processing.
        
        Args:
            documents: List of document dictionaries with 'page_content' and 'metadata'
            chunk_size: Maximum size of each chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of document chunks
        """
        logger.info(f"Splitting {len(documents)} documents into chunks")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            add_start_index=True,
            strip_whitespace=True
        )
        
        splits = []
        for doc in documents:
            # Clean the text before splitting
            clean_text = TextCleaner.clean_text(doc["page_content"])
            
            # Split the text
            split_texts = text_splitter.split_text(clean_text)
            
            # Create new document chunks
            for i, split_text in enumerate(split_texts):
                split_doc = {
                    "page_content": split_text,
                    "metadata": {
                        **doc["metadata"],
                        "chunk_index": i
                    }
                }
                splits.append(split_doc)
        
        logger.info(f"Created {len(splits)} document chunks")
        return splits
    
    @staticmethod
    def process_text(documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process text by dynamically determining chunk parameters and splitting.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            List of processed and split document chunks
        """
        # Calculate average text length
        avg_length = TextCleaner.calculate_avg_text_length(documents)
        
        # Determine chunk parameters based on text length
        chunk_size, chunk_overlap = TextCleaner.determine_chunk_parameters(avg_length)
        
        # Split documents using determined parameters
        splits = TextCleaner.split_documents(documents, chunk_size, chunk_overlap)
        
        return splits
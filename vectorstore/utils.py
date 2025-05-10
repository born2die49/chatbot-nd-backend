import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

def format_metadata(document_id: str, chunk_id: str, chunk_index: int, page_number: int = None) -> Dict[str, Any]:
    """Format metadata for vector store entries.
    
    Args:
        document_id: ID of the document
        chunk_id: ID of the document chunk
        chunk_index: Index of the chunk within the document
        page_number: Optional page number
        
    Returns:
        Dictionary of metadata
    """
    metadata = {
        'document_id': document_id,
        'chunk_id': chunk_id,
        'chunk_index': chunk_index
    }
    
    if page_number is not None:
        metadata['page_number'] = page_number
        
    return metadata
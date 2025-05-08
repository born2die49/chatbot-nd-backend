import tempfile
import uuid
import logging
from typing import List, Dict, Any
import os

from langchain_community.document_loaders import PyPDFLoader

logger = logging.getLogger(__name__)

class InvalidFileFormatError(Exception):
    """Exception raised when an invalid file format is provided."""
    pass

class DocumentExtractionError(Exception):
    """Exception raised when document extraction fails."""
    pass

class PDFExtractor:
    """Utility class to extract content from PDF files."""
    
    @staticmethod
    def extract_from_file(file_path: str) -> List[Dict[str, Any]]:
        """Extract content from a PDF file on disk.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            List of dictionaries containing page content and metadata
        """
        logger.info(f"Extracting content from PDF file: {file_path}")
        
        if not file_path.lower().endswith('.pdf'):
            logger.error(f"Invalid file format: {file_path}. Only PDF files are supported")
            raise InvalidFileFormatError("Only PDF files are supported")
        
        try:
            # Use PyPDFLoader to extract document content
            logger.debug(f"Loading PDF using PyPDFLoader: {file_path}")
            loader = PyPDFLoader(file_path)
            docs = loader.load()
            
            if not docs:
                logger.warning(f"No content extracted from PDF: {file_path}")
                raise DocumentExtractionError("No content extracted from PDF")
            
            logger.info(f"Successfully extracted {len(docs)} pages from {file_path}")
            
            # Convert to standard format
            processed_docs = []
            doc_uuid = str(uuid.uuid4())
            
            for doc in docs:
                processed_doc = {
                    "page_content": doc.page_content,
                    "metadata": {
                        "doc_uuid": doc_uuid,
                        "source": os.path.basename(file_path),
                        "page": doc.metadata.get("page", 0)
                    }
                }
                processed_docs.append(processed_doc)
            
            logger.info(f"Created {len(processed_docs)} document chunks from {file_path}")
            return processed_docs
            
        except Exception as e:
            logger.exception(f"Error extracting content from PDF: {str(e)}")
            raise DocumentExtractionError(f"Failed to extract content: {str(e)}")
    
    @staticmethod
    def extract_from_bytes(file_content: bytes, file_name: str) -> List[Dict[str, Any]]:
        """Extract content from PDF file bytes.
        
        Args:
            file_content: Bytes content of the PDF file
            file_name: Name of the file
            
        Returns:
            List of dictionaries containing page content and metadata
        """
        logger.info(f"Extracting content from PDF bytes: {file_name}")
        
        if not file_name.lower().endswith('.pdf'):
            logger.error(f"Invalid file format: {file_name}. Only PDF files are supported")
            raise InvalidFileFormatError("Only PDF files are supported")
        
        try:
            # Save file content to a temporary file
            logger.debug(f"Creating temporary file for {file_name}")
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
                temp_file.write(file_content)
                temp_path = temp_file.name
                logger.debug(f"Temporary file created at: {temp_path}")
            
            # Extract content using the file-based method
            results = PDFExtractor.extract_from_file(temp_path)
            
            # Clean up the temporary file
            try:
                os.unlink(temp_path)
                logger.debug(f"Temporary file removed: {temp_path}")
            except Exception as e:
                logger.warning(f"Failed to remove temporary file {temp_path}: {str(e)}")
            
            return results
            
        except Exception as e:
            logger.exception(f"Error extracting content from PDF bytes: {str(e)}")
            raise DocumentExtractionError(f"Failed to extract content: {str(e)}")
"""Document processing pipeline for RAG knowledge base."""

import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import PyPDF2
from docx import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import BaseModel

from config.settings import settings

logger = logging.getLogger(__name__)


class DocumentChunk(BaseModel):
    """Represents a processed document chunk."""
    
    id: str
    content: str
    metadata: Dict[str, str]
    source_file: str
    chunk_index: int


class DocumentProcessor:
    """Processes documents for RAG knowledge base ingestion."""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        """Initialize the document processor.
        
        Args:
            chunk_size: Size of text chunks (defaults to settings)
            chunk_overlap: Overlap between chunks (defaults to settings)
        """
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def process_pdf(self, file_path: Path) -> str:
        """Extract text from PDF file.
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text content
        """
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = []
                
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_content.append(f"[Page {page_num + 1}]\n{page_text}")
                
                return "\n\n".join(text_content)
                
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {e}")
            raise
    
    def process_docx(self, file_path: Path) -> str:
        """Extract text from DOCX file.
        
        Args:
            file_path: Path to DOCX file
            
        Returns:
            Extracted text content
        """
        try:
            doc = Document(file_path)
            paragraphs = []
            
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    paragraphs.append(paragraph.text)
            
            return "\n\n".join(paragraphs)
            
        except Exception as e:
            logger.error(f"Error processing DOCX {file_path}: {e}")
            raise
    
    def process_txt(self, file_path: Path) -> str:
        """Extract text from TXT file.
        
        Args:
            file_path: Path to TXT file
            
        Returns:
            File content
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            logger.error(f"Error processing TXT {file_path}: {e}")
            raise
    
    def extract_text(self, file_path: Path) -> str:
        """Extract text from supported file formats.
        
        Args:
            file_path: Path to document file
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If file format is not supported
        """
        file_extension = file_path.suffix.lower()
        
        if file_extension == '.pdf':
            return self.process_pdf(file_path)
        elif file_extension == '.docx':
            return self.process_docx(file_path)
        elif file_extension == '.txt':
            return self.process_txt(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")
    
    def create_chunks(self, text: str, source_file: str, metadata: Optional[Dict[str, str]] = None) -> List[DocumentChunk]:
        """Split text into chunks for RAG processing.
        
        Args:
            text: Text content to chunk
            source_file: Source file path
            metadata: Additional metadata for chunks
            
        Returns:
            List of document chunks
        """
        if metadata is None:
            metadata = {}
        
        # Add source file to metadata
        base_metadata = {
            "source": source_file,
            "document_type": Path(source_file).suffix.lower(),
            **metadata
        }
        
        # Split text into chunks
        text_chunks = self.text_splitter.split_text(text)
        
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            # Create unique chunk ID
            chunk_id = self._generate_chunk_id(source_file, i, chunk_text)
            
            # Create chunk metadata
            chunk_metadata = {
                **base_metadata,
                "chunk_index": str(i),
                "total_chunks": str(len(text_chunks))
            }
            
            chunk = DocumentChunk(
                id=chunk_id,
                content=chunk_text.strip(),
                metadata=chunk_metadata,
                source_file=source_file,
                chunk_index=i
            )
            chunks.append(chunk)
        
        return chunks
    
    def process_document(self, file_path: Path, metadata: Optional[Dict[str, str]] = None) -> List[DocumentChunk]:
        """Process a document file into chunks.
        
        Args:
            file_path: Path to document file
            metadata: Additional metadata for the document
            
        Returns:
            List of processed document chunks
        """
        logger.info(f"Processing document: {file_path}")
        
        try:
            # Extract text
            text = self.extract_text(file_path)
            
            # Create chunks
            chunks = self.create_chunks(text, str(file_path), metadata)
            
            logger.info(f"Successfully processed {file_path}: {len(chunks)} chunks created")
            return chunks
            
        except Exception as e:
            logger.error(f"Failed to process document {file_path}: {e}")
            raise
    
    def process_directory(self, directory_path: Path, metadata: Optional[Dict[str, str]] = None) -> List[DocumentChunk]:
        """Process all supported documents in a directory.
        
        Args:
            directory_path: Path to directory containing documents
            metadata: Additional metadata for all documents
            
        Returns:
            List of all processed document chunks
        """
        supported_extensions = {'.pdf', '.docx', '.txt'}
        all_chunks = []
        
        for file_path in directory_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                try:
                    chunks = self.process_document(file_path, metadata)
                    all_chunks.extend(chunks)
                except Exception as e:
                    logger.error(f"Skipping file {file_path} due to error: {e}")
                    continue
        
        logger.info(f"Processed directory {directory_path}: {len(all_chunks)} total chunks")
        return all_chunks
    
    def _generate_chunk_id(self, source_file: str, chunk_index: int, content: str) -> str:
        """Generate unique ID for a document chunk.
        
        Args:
            source_file: Source file path
            chunk_index: Index of chunk in document
            content: Chunk content
            
        Returns:
            Unique chunk ID
        """
        # Create hash from source file, index, and content
        hash_input = f"{source_file}:{chunk_index}:{content[:100]}"
        return hashlib.md5(hash_input.encode()).hexdigest()


# Global document processor instance
document_processor = DocumentProcessor()

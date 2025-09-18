"""Knowledge base manager for RAG system."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from .document_processor import DocumentProcessor, DocumentChunk
from .vector_store import VectorStore, SearchResult
from config.settings import settings

logger = logging.getLogger(__name__)


class KnowledgeBase:
    """Manages the RAG knowledge base including document processing and vector storage."""
    
    def __init__(self):
        """Initialize the knowledge base."""
        self.document_processor = DocumentProcessor()
        self.vector_store = VectorStore()
    
    def ingest_document(self, file_path: Path, metadata: Optional[Dict[str, str]] = None) -> int:
        """Ingest a single document into the knowledge base.
        
        Args:
            file_path: Path to the document file
            metadata: Optional metadata for the document
            
        Returns:
            Number of chunks created and stored
        """
        logger.info(f"Ingesting document: {file_path}")
        
        try:
            # Process document into chunks
            chunks = self.document_processor.process_document(file_path, metadata)
            
            # Add chunks to vector store
            self.vector_store.add_chunks(chunks)
            
            logger.info(f"Successfully ingested {file_path}: {len(chunks)} chunks")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Failed to ingest document {file_path}: {e}")
            raise
    
    def ingest_directory(self, directory_path: Path, metadata: Optional[Dict[str, str]] = None) -> int:
        """Ingest all supported documents from a directory.
        
        Args:
            directory_path: Path to directory containing documents
            metadata: Optional metadata for all documents
            
        Returns:
            Total number of chunks created and stored
        """
        logger.info(f"Ingesting directory: {directory_path}")
        
        try:
            # Process all documents in directory
            chunks = self.document_processor.process_directory(directory_path, metadata)
            
            # Add chunks to vector store
            self.vector_store.add_chunks(chunks)
            
            logger.info(f"Successfully ingested directory {directory_path}: {len(chunks)} total chunks")
            return len(chunks)
            
        except Exception as e:
            logger.error(f"Failed to ingest directory {directory_path}: {e}")
            raise
    
    def search(
        self, 
        query: str, 
        n_results: int = None,
        filter_by: Optional[Dict[str, str]] = None
    ) -> List[SearchResult]:
        """Search the knowledge base for relevant information.
        
        Args:
            query: Search query
            n_results: Number of results to return
            filter_by: Optional metadata filters
            
        Returns:
            List of relevant search results
        """
        return self.vector_store.search(query, n_results, filter_by)
    
    def get_context_for_query(self, query: str, max_context_length: int = 4000) -> str:
        """Get relevant context for a query, formatted for LLM consumption.
        
        Args:
            query: Search query
            max_context_length: Maximum length of context to return
            
        Returns:
            Formatted context string
        """
        results = self.search(query)
        
        if not results:
            return "No relevant information found in the knowledge base."
        
        context_parts = []
        current_length = 0
        
        for i, result in enumerate(results):
            # Format each result
            result_text = f"[Source {i+1}: {result.metadata.get('source', 'Unknown')}]\n{result.content}\n"
            
            # Check if adding this result would exceed the limit
            if current_length + len(result_text) > max_context_length:
                break
            
            context_parts.append(result_text)
            current_length += len(result_text)
        
        return "\n---\n".join(context_parts)
    
    def get_offering_info(self, offering_name: str) -> List[SearchResult]:
        """Get specific information about a D&T offering.
        
        Args:
            offering_name: Name of the offering to search for
            
        Returns:
            List of relevant results about the offering
        """
        # Search for the specific offering
        query = f"{offering_name} offering service solution"
        return self.search(query, n_results=3)
    
    def get_similar_solutions(self, problem_description: str) -> List[SearchResult]:
        """Find solutions similar to a described problem.
        
        Args:
            problem_description: Description of the client's problem
            
        Returns:
            List of relevant solutions
        """
        # Search for solutions related to the problem
        query = f"solution for {problem_description} problem challenge"
        return self.search(query, n_results=5)
    
    def get_stats(self) -> Dict[str, any]:
        """Get knowledge base statistics.
        
        Returns:
            Dictionary with knowledge base statistics
        """
        collection_info = self.vector_store.get_collection_info()
        
        return {
            "total_chunks": collection_info["count"],
            "collection_name": collection_info["name"],
            "embedding_model": settings.embedding_model,
            "chunk_size": settings.chunk_size,
            "chunk_overlap": settings.chunk_overlap
        }
    
    def reset(self) -> None:
        """Reset the entire knowledge base. Use with caution!"""
        logger.warning("Resetting knowledge base - all data will be lost!")
        self.vector_store.reset_collection()
        logger.info("Knowledge base reset complete")
    
    def health_check(self) -> Dict[str, any]:
        """Perform a health check on the knowledge base.
        
        Returns:
            Health check results
        """
        try:
            # Test basic search functionality
            test_results = self.search("test", n_results=1)
            
            stats = self.get_stats()
            
            return {
                "status": "healthy",
                "total_chunks": stats["total_chunks"],
                "search_functional": True,
                "vector_store_accessible": True
            }
            
        except Exception as e:
            logger.error(f"Knowledge base health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "search_functional": False,
                "vector_store_accessible": False
            }


# Global knowledge base instance
knowledge_base = KnowledgeBase()

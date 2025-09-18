"""Vector store management using Chroma for RAG knowledge base."""

import os
import logging
from typing import Dict, List, Optional, Tuple

# Disable ChromaDB telemetry before importing
os.environ['CHROMA_TELEMETRY_DISABLED'] = 'true'
os.environ['ANONYMIZED_TELEMETRY'] = 'false'

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel

from config.settings import settings
from .document_processor import DocumentChunk

logger = logging.getLogger(__name__)


class SearchResult(BaseModel):
    """Represents a search result from the vector store."""
    
    id: str
    content: str
    metadata: Dict[str, str]
    score: float


class VectorStore:
    """Manages the vector database for RAG knowledge base."""
    
    def __init__(self, collection_name: str = "sg_dt_offerings"):
        """Initialize the vector store.
        
        Args:
            collection_name: Name of the Chroma collection
        """
        self.collection_name = collection_name
        self.embedding_model = SentenceTransformer(settings.embedding_model)
        
        # Initialize Chroma client
        self.chroma_client = chromadb.PersistentClient(
            path=settings.chroma_persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(name=collection_name)
            logger.info(f"Loaded existing collection: {collection_name}")
        except Exception:
            # Collection doesn't exist, create it
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "SG D&T Offerings Knowledge Base"}
            )
            logger.info(f"Created new collection: {collection_name}")
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts using SentenceTransformers.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            embeddings = self.embedding_model.encode(texts, convert_to_tensor=False)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """Add document chunks to the vector store.
        
        Args:
            chunks: List of document chunks to add
        """
        if not chunks:
            logger.warning("No chunks provided to add to vector store")
            return
        
        logger.info(f"Adding {len(chunks)} chunks to vector store")
        
        try:
            # Prepare data for Chroma
            ids = [chunk.id for chunk in chunks]
            documents = [chunk.content for chunk in chunks]
            metadatas = [chunk.metadata for chunk in chunks]
            
            # Generate embeddings
            embeddings = self.get_embeddings(documents)
            
            # Add to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully added {len(chunks)} chunks to vector store")
            
        except Exception as e:
            logger.error(f"Error adding chunks to vector store: {e}")
            raise
    
    def search(
        self, 
        query: str, 
        n_results: int = None,
        filter_metadata: Optional[Dict[str, str]] = None
    ) -> List[SearchResult]:
        """Search the vector store for relevant documents.
        
        Args:
            query: Search query
            n_results: Number of results to return (defaults to settings)
            filter_metadata: Optional metadata filters
            
        Returns:
            List of search results
        """
        n_results = n_results or settings.max_retrieval_results
        
        try:
            # Generate query embedding
            query_embedding = self.get_embeddings([query])[0]
            
            # Search the collection
            search_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata,
                include=["documents", "metadatas", "distances"]
            )
            
            # Convert to SearchResult objects
            results = []
            if search_results['ids'] and search_results['ids'][0]:
                for i in range(len(search_results['ids'][0])):
                    result = SearchResult(
                        id=search_results['ids'][0][i],
                        content=search_results['documents'][0][i],
                        metadata=search_results['metadatas'][0][i],
                        score=1.0 - search_results['distances'][0][i]  # Convert distance to similarity score
                    )
                    results.append(result)
            
            logger.info(f"Search query '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error searching vector store: {e}")
            raise
    
    def get_collection_info(self) -> Dict[str, any]:
        """Get information about the collection.
        
        Returns:
            Collection information including count and metadata
        """
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "count": count,
                "metadata": self.collection.metadata
            }
        except Exception as e:
            logger.error(f"Error getting collection info: {e}")
            return {"name": self.collection_name, "count": 0, "metadata": {}}
    
    def delete_collection(self) -> None:
        """Delete the entire collection. Use with caution!"""
        try:
            self.chroma_client.delete_collection(name=self.collection_name)
            logger.info(f"Deleted collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
            raise
    
    def reset_collection(self) -> None:
        """Reset the collection by deleting and recreating it."""
        try:
            self.delete_collection()
            self.collection = self.chroma_client.create_collection(
                name=self.collection_name,
                metadata={"description": "SG D&T Offerings Knowledge Base"}
            )
            logger.info(f"Reset collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error resetting collection: {e}")
            raise
    
    def update_chunk(self, chunk: DocumentChunk) -> None:
        """Update an existing chunk in the vector store.
        
        Args:
            chunk: Updated document chunk
        """
        try:
            # Generate new embedding
            embedding = self.get_embeddings([chunk.content])[0]
            
            # Update in collection
            self.collection.update(
                ids=[chunk.id],
                embeddings=[embedding],
                documents=[chunk.content],
                metadatas=[chunk.metadata]
            )
            
            logger.info(f"Updated chunk: {chunk.id}")
            
        except Exception as e:
            logger.error(f"Error updating chunk {chunk.id}: {e}")
            raise
    
    def delete_chunks(self, chunk_ids: List[str]) -> None:
        """Delete chunks from the vector store.
        
        Args:
            chunk_ids: List of chunk IDs to delete
        """
        try:
            self.collection.delete(ids=chunk_ids)
            logger.info(f"Deleted {len(chunk_ids)} chunks from vector store")
        except Exception as e:
            logger.error(f"Error deleting chunks: {e}")
            raise


# Global vector store instance
vector_store = VectorStore()

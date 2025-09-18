#!/usr/bin/env python3
"""Knowledge base management CLI tool."""

import argparse
import logging
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.rag.knowledge_base import knowledge_base
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ingest_documents(documents_path: str) -> None:
    """Ingest documents from a directory or file."""
    path = Path(documents_path)
    
    if not path.exists():
        logger.error(f"Path does not exist: {path}")
        return
    
    try:
        if path.is_file():
            chunks_count = knowledge_base.ingest_document(path)
            print(f"✅ Successfully ingested {path}")
            print(f"📄 Created {chunks_count} chunks")
        else:
            chunks_count = knowledge_base.ingest_directory(path)
            print(f"✅ Successfully ingested directory {path}")
            print(f"📄 Created {chunks_count} total chunks")
        
        # Show updated stats
        stats = knowledge_base.get_stats()
        print(f"📊 Total chunks in knowledge base: {stats['total_chunks']}")
        
    except Exception as e:
        logger.error(f"Failed to ingest documents: {e}")
        print(f"❌ Ingestion failed: {e}")


def search_knowledge_base(query: str, num_results: int = 3) -> None:
    """Search the knowledge base."""
    try:
        results = knowledge_base.search(query, n_results=num_results)
        
        if not results:
            print(f"❌ No results found for query: '{query}'")
            return
        
        print(f"🔍 Search results for: '{query}'")
        print("=" * 50)
        
        for i, result in enumerate(results, 1):
            print(f"\n📄 Result {i} (Score: {result.score:.3f})")
            print(f"📁 Source: {result.metadata.get('source', 'Unknown')}")
            print(f"📝 Content: {result.content[:300]}...")
            print("-" * 30)
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        print(f"❌ Search failed: {e}")


def show_stats() -> None:
    """Show knowledge base statistics."""
    try:
        stats = knowledge_base.get_stats()
        health = knowledge_base.health_check()
        
        print("📊 Knowledge Base Statistics")
        print("=" * 30)
        print(f"Status: {'✅ Healthy' if health['status'] == 'healthy' else '❌ Unhealthy'}")
        print(f"Total chunks: {stats['total_chunks']}")
        print(f"Collection: {stats['collection_name']}")
        print(f"Embedding model: {stats['embedding_model']}")
        print(f"Chunk size: {stats['chunk_size']}")
        print(f"Chunk overlap: {stats['chunk_overlap']}")
        
        if health['status'] != 'healthy':
            print(f"❌ Error: {health.get('error', 'Unknown error')}")
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        print(f"❌ Failed to get stats: {e}")


def reset_knowledge_base() -> None:
    """Reset the knowledge base."""
    confirm = input("⚠️  This will delete ALL data in the knowledge base. Type 'CONFIRM' to proceed: ")
    
    if confirm != "CONFIRM":
        print("❌ Reset cancelled")
        return
    
    try:
        knowledge_base.reset()
        print("✅ Knowledge base reset successfully")
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        print(f"❌ Reset failed: {e}")


def main():
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Manage the SG D&T AI Co-Pilot knowledge base")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Ingest command
    ingest_parser = subparsers.add_parser('ingest', help='Ingest documents into the knowledge base')
    ingest_parser.add_argument('path', help='Path to document file or directory')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search the knowledge base')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--results', '-n', type=int, default=3, help='Number of results to return')
    
    # Stats command
    subparsers.add_parser('stats', help='Show knowledge base statistics')
    
    # Reset command
    subparsers.add_parser('reset', help='Reset the knowledge base (deletes all data)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Check if .env file exists
    env_file = Path('.env')
    if not env_file.exists():
        print("⚠️  No .env file found. Please create one based on .env.example")
        print("   Make sure to set your OPENAI_API_KEY")
        return
    
    # Execute command
    if args.command == 'ingest':
        ingest_documents(args.path)
    elif args.command == 'search':
        search_knowledge_base(args.query, args.results)
    elif args.command == 'stats':
        show_stats()
    elif args.command == 'reset':
        reset_knowledge_base()


if __name__ == "__main__":
    main()

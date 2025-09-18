"""Application configuration settings."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application
    app_name: str = Field(default="SG D&T AI Co-Pilot", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    
    # Google Gemini Configuration
    google_api_key: str = Field(..., description="Google API key for Gemini")
    gemini_model: str = Field(default="gemini-1.5-flash", description="Gemini model name")
    
    # Groq Configuration (Fallback)
    groq_api_key: str = Field(..., description="Groq API key for fallback")
    groq_model: str = Field(default="llama-3.1-8b-instant", description="Groq model name")
    
    # Database Configuration
    database_url: str = Field(default="sqlite:///./copilot.db", description="Database URL")
    
    # RAG Configuration
    chroma_persist_directory: str = Field(default="./chroma_db", description="Chroma database directory")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="Sentence transformers embedding model")
    chunk_size: int = Field(default=1000, description="Text chunk size for RAG")
    chunk_overlap: int = Field(default=200, description="Text chunk overlap")
    max_retrieval_results: int = Field(default=5, description="Maximum RAG retrieval results")
    
    # ChromaDB Configuration
    chroma_telemetry_disabled: bool = Field(default=True, description="Disable ChromaDB telemetry")
    anonymized_telemetry: bool = Field(default=False, description="Disable anonymized telemetry")
    
    # Security
    secret_key: str = Field(..., description="Secret key for JWT tokens")
    
    @property
    def project_root(self) -> Path:
        """Get the project root directory."""
        return Path(__file__).parent.parent
    
    @property
    def data_directory(self) -> Path:
        """Get the data directory path."""
        return self.project_root / "data"
    
    @property
    def documents_directory(self) -> Path:
        """Get the documents directory path."""
        return self.data_directory / "documents"
    
    @property
    def processed_directory(self) -> Path:
        """Get the processed documents directory path."""
        return self.data_directory / "processed"


# Global settings instance
settings = Settings()

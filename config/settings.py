"""
Configuration settings for the Document Helper System.
"""
import os
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # OpenAI settings
    openai_api_key: str = Field(default="", env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    embedding_model: str = Field(default="text-embedding-3-small", env="EMBEDDING_MODEL")
    
    # Paths
    base_dir: str = Field(default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    upload_dir: str = Field(default="")
    vectordb_dir: str = Field(default="")
    knowledge_dir: str = Field(default="")
    
    # RAG settings
    chunk_size: int = Field(default=500, env="CHUNK_SIZE")
    chunk_overlap: int = Field(default=100, env="CHUNK_OVERLAP")
    top_k_retrieval: int = Field(default=5, env="TOP_K_RETRIEVAL")
    
    # OCR settings
    tesseract_cmd: Optional[str] = Field(default=None, env="TESSERACT_CMD")
    ocr_lang: str = Field(default="kor+eng", env="OCR_LANG")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set default paths after base_dir is resolved
        if not self.upload_dir:
            self.upload_dir = os.path.join(self.base_dir, "data", "uploads")
        if not self.vectordb_dir:
            self.vectordb_dir = os.path.join(self.base_dir, "data", "vectordb")
        if not self.knowledge_dir:
            self.knowledge_dir = os.path.join(self.base_dir, "data", "knowledge_base")
        
        # Create directories if they don't exist
        os.makedirs(self.upload_dir, exist_ok=True)
        os.makedirs(self.vectordb_dir, exist_ok=True)
        os.makedirs(self.knowledge_dir, exist_ok=True)


# Global settings instance
settings = Settings()

"""
Embeddings Module

Generates embeddings using OpenAI API.
"""
import os
from typing import List, Optional

from openai import OpenAI

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings


class EmbeddingGenerator:
    """
    Generates text embeddings using OpenAI's embedding models.
    """
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize the embedding generator.
        
        Args:
            model: Embedding model to use
        """
        self.model = model or settings.embedding_model
        self.client = OpenAI(api_key=settings.openai_api_key)
    
    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        # Clean and truncate text if needed
        text = text.replace("\n", " ").strip()
        if len(text) > 8000:
            text = text[:8000]
        
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        
        return response.data[0].embedding
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        if not texts:
            return []
        
        # Clean texts
        cleaned = []
        for text in texts:
            t = text.replace("\n", " ").strip()
            if len(t) > 8000:
                t = t[:8000]
            cleaned.append(t)
        
        # Batch embed (OpenAI supports batching)
        response = self.client.embeddings.create(
            model=self.model,
            input=cleaned
        )
        
        return [d.embedding for d in response.data]
    
    @property
    def embedding_dimension(self) -> int:
        """Get embedding dimension for the current model."""
        if "text-embedding-3-small" in self.model:
            return 1536
        elif "text-embedding-3-large" in self.model:
            return 3072
        elif "text-embedding-ada-002" in self.model:
            return 1536
        else:
            return 1536  # Default

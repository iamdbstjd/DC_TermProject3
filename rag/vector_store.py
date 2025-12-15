"""
Vector Store Module

Manages vector storage and retrieval using ChromaDB.
"""
import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
import uuid

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from .embeddings import EmbeddingGenerator


class VectorStore:
    """
    Vector database wrapper using ChromaDB for document storage and retrieval.
    """
    
    def __init__(
        self,
        collection_name: str = "doc_helper_knowledge",
        persist_directory: Optional[str] = None
    ):
        """
        Initialize the vector store.
        
        Args:
            collection_name: Name of the ChromaDB collection
            persist_directory: Directory to persist the database
        """
        self.persist_directory = persist_directory or settings.vectordb_dir
        
        # Ensure directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(
                anonymized_telemetry=False
            )
        )
        
        # Get or create collection
        self.collection_name = collection_name
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        # Initialize embedding generator
        self.embedder = EmbeddingGenerator()
    
    def add_documents(
        self,
        texts: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to the vector store.
        
        Args:
            texts: List of document texts
            metadatas: Optional list of metadata dicts
            ids: Optional list of document IDs
            
        Returns:
            List of document IDs
        """
        if not texts:
            return []
        
        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        
        # Generate embeddings
        embeddings = self.embedder.embed_texts(texts)
        
        # Prepare metadatas
        if metadatas is None:
            metadatas = [{}] * len(texts)
        
        # Ensure all metadata values are JSON-serializable primitives
        clean_metadatas = []
        for meta in metadatas:
            clean_meta = {}
            for k, v in meta.items():
                if isinstance(v, (str, int, float, bool)):
                    clean_meta[k] = v
                elif v is None:
                    clean_meta[k] = ""
                else:
                    clean_meta[k] = str(v)
            clean_metadatas.append(clean_meta)
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=clean_metadatas
        )
        
        return ids
    
    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query text
            n_results: Number of results to return
            filter_metadata: Optional metadata filter
            
        Returns:
            List of search results with text, metadata, and score
        """
        # Generate query embedding
        query_embedding = self.embedder.embed_text(query)
        
        # Perform search
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_metadata
        )
        
        # Format results
        formatted_results = []
        if results['ids'] and results['ids'][0]:
            for i in range(len(results['ids'][0])):
                formatted_results.append({
                    "id": results['ids'][0][i],
                    "text": results['documents'][0][i] if results['documents'] else "",
                    "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                    "distance": results['distances'][0][i] if results['distances'] else 0.0,
                    "score": 1 - results['distances'][0][i] if results['distances'] else 1.0
                })
        
        return formatted_results
    
    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID."""
        results = self.collection.get(ids=[doc_id])
        
        if results['ids']:
            return {
                "id": results['ids'][0],
                "text": results['documents'][0] if results['documents'] else "",
                "metadata": results['metadatas'][0] if results['metadatas'] else {}
            }
        return None
    
    def delete_document(self, doc_id: str):
        """Delete a document by ID."""
        self.collection.delete(ids=[doc_id])
    
    def delete_collection(self):
        """Delete the entire collection."""
        self.client.delete_collection(self.collection_name)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get collection statistics."""
        return {
            "collection_name": self.collection_name,
            "count": self.collection.count(),
            "persist_directory": self.persist_directory
        }
    
    def list_all_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all documents in the collection."""
        results = self.collection.get(limit=limit)
        
        documents = []
        for i in range(len(results['ids'])):
            documents.append({
                "id": results['ids'][i],
                "text": results['documents'][i] if results['documents'] else "",
                "metadata": results['metadatas'][i] if results['metadatas'] else {}
            })
        
        return documents

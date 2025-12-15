"""
RAG Agent Module

Retrieves relevant context from knowledge base.
"""
import os
from typing import Dict, Any, List, Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_agent import BaseAgent


class RAGAgent(BaseAgent):
    """
    Agent for retrieving relevant information from knowledge base.
    Uses vector similarity search.
    """
    
    def __init__(self, collection_name: str = "doc_helper_knowledge"):
        super().__init__()
        self.collection_name = collection_name
        self._vector_store = None
    
    @property
    def vector_store(self):
        """Lazy load vector store."""
        if self._vector_store is None:
            from rag import VectorStore
            self._vector_store = VectorStore(collection_name=self.collection_name)
        return self._vector_store
    
    def process(
        self,
        doc_type: str,
        key_info: Dict[str, Any],
        ocr_text: str = "",
        top_k: int = 5,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Retrieve relevant context for the document.
        
        Args:
            doc_type: Classified document type
            key_info: Extracted key information
            ocr_text: Original OCR text for additional context
            top_k: Number of results to retrieve
            
        Returns:
            Retrieved context with sources
        """
        # Build search query
        query = self._build_query(doc_type, key_info)
        
        # Search vector store
        try:
            results = self.vector_store.search(query, n_results=top_k)
            
            # Format results
            retrieved_chunks = []
            for r in results:
                retrieved_chunks.append({
                    "text": r.get("text", ""),
                    "source": r.get("metadata", {}).get("source_name", "Unknown"),
                    "doc_type": r.get("metadata", {}).get("doc_type", ""),
                    "topic": r.get("metadata", {}).get("topic", ""),
                    "score": r.get("score", 0.0)
                })
            
            # Generate summary using LLM if we have results
            summary = ""
            if retrieved_chunks:
                summary = self._generate_summary(doc_type, key_info, retrieved_chunks)
            
            return {
                "retrieved_chunks": retrieved_chunks,
                "query": query,
                "summary": summary
            }
            
        except Exception as e:
            # Return empty if vector store not available
            return {
                "retrieved_chunks": [],
                "query": query,
                "summary": "",
                "error": str(e)
            }
    
    def _build_query(self, doc_type: str, key_info: Dict[str, Any]) -> str:
        """Build search query from document info."""
        query_parts = [doc_type]
        
        if key_info.get("organization"):
            query_parts.append(key_info["organization"])
        
        if key_info.get("action_required"):
            query_parts.append("처리방법 절차 안내")
        
        if key_info.get("penalty_risk") in ["MEDIUM", "HIGH"]:
            query_parts.append("연체 불이익 주의사항")
        
        return " ".join(query_parts)
    
    def _generate_summary(
        self,
        doc_type: str,
        key_info: Dict[str, Any],
        chunks: List[Dict]
    ) -> str:
        """Generate summary from retrieved chunks."""
        
        context = "\n".join([
            f"[{c['source']}] {c['text'][:500]}"
            for c in chunks[:3]
        ])
        
        if not context:
            return ""
        
        system_prompt = """당신은 공공문서 안내 전문가입니다.
검색된 정보를 바탕으로 사용자에게 도움이 될 요약을 제공하세요.
쉬운 말로 간결하게 2-3문장으로 요약하세요."""

        user_prompt = f"""문서 유형: {doc_type}
핵심 정보: {key_info}

관련 참고 정보:
{context}

위 정보를 바탕으로 이 문서에 대한 일반적인 안내를 요약해주세요."""

        return self._call_llm(system_prompt, user_prompt, max_tokens=300)
    
    def add_knowledge(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]]
    ) -> List[str]:
        """Add knowledge to the vector store."""
        return self.vector_store.add_documents(texts, metadatas)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        try:
            return self.vector_store.get_stats()
        except Exception:
            return {"count": 0, "error": "Vector store not initialized"}

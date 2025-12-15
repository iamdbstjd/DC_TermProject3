"""
Knowledge Base Loader

Loads and indexes knowledge data into the vector store.
Updated for v2.0 format with action guides.
"""
import os
import json
from typing import List, Dict, Any

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from rag import VectorStore


def load_knowledge_base(json_path: str = None, collection_name: str = "doc_helper_knowledge") -> int:
    """
    Load knowledge base from JSON file into vector store.
    
    Args:
        json_path: Path to knowledge JSON file
        collection_name: Name of the vector store collection
        
    Returns:
        Number of items loaded
    """
    if json_path is None:
        json_path = os.path.join(settings.knowledge_dir, "knowledge_data.json")
    
    if not os.path.exists(json_path):
        print(f"Knowledge file not found: {json_path}")
        return 0
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    items = data.get("knowledge_items", [])
    if not items:
        print("No knowledge items found in file")
        return 0
    
    # Initialize vector store
    vector_store = VectorStore(collection_name=collection_name)
    
    # Prepare documents - include action guide in searchable text
    texts = []
    metadatas = []
    ids = []
    
    for item in items:
        # Build comprehensive text for embedding
        text_parts = [item.get("text", "")]
        
        # Add action guide info to searchable text
        action_guide = item.get("action_guide", {})
        if action_guide:
            if action_guide.get("phone"):
                phone_info = action_guide["phone"]
                text_parts.append(f"연락처: {phone_info.get('number', '')}")
            if action_guide.get("online"):
                online_info = action_guide["online"]
                text_parts.append(f"홈페이지: {online_info.get('url', '')}")
            if action_guide.get("visit"):
                visit_info = action_guide["visit"]
                text_parts.append(f"방문: {visit_info.get('place', '')}")
        
        full_text = " ".join(text_parts)
        texts.append(full_text)
        
        # Store metadata including action_guide as JSON string
        metadatas.append({
            "domain": item.get("domain", ""),
            "doc_type": item.get("doc_type", ""),
            "scenario": item.get("scenario", ""),
            "topic": item.get("topic", ""),
            "source_name": item.get("source_name", ""),
            "source_url": item.get("source_url", ""),
            "action_guide": json.dumps(item.get("action_guide", {}), ensure_ascii=False)
        })
        ids.append(item.get("id", ""))
    
    # Add to vector store
    vector_store.add_documents(texts, metadatas, ids)
    
    print(f"Loaded {len(texts)} knowledge items into vector store")
    return len(texts)


def get_contact_info(domain: str, json_path: str = None) -> Dict[str, Any]:
    """
    Get contact information for a specific domain.
    
    Args:
        domain: Domain name (국민연금공단, 국민건강보험공단, 보건복지상담센터, 국세상담센터)
        json_path: Path to knowledge JSON file
        
    Returns:
        Contact information dict
    """
    if json_path is None:
        json_path = os.path.join(settings.knowledge_dir, "knowledge_data.json")
    
    if not os.path.exists(json_path):
        return {}
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    contact_summary = data.get("contact_summary", {})
    return contact_summary.get(domain, {})


def get_all_contacts(json_path: str = None) -> Dict[str, Any]:
    """Get all contact information."""
    if json_path is None:
        json_path = os.path.join(settings.knowledge_dir, "knowledge_data.json")
    
    if not os.path.exists(json_path):
        return {}
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    return data.get("contact_summary", {})


def check_knowledge_base(collection_name: str = "doc_helper_knowledge") -> Dict[str, Any]:
    """Check current knowledge base status."""
    try:
        vector_store = VectorStore(collection_name=collection_name)
        return vector_store.get_stats()
    except Exception as e:
        return {"error": str(e)}


def search_knowledge(
    query: str, 
    domain: str = None, 
    top_k: int = 3,
    collection_name: str = "doc_helper_knowledge"
) -> List[Dict[str, Any]]:
    """
    Search knowledge base with optional domain filter.
    
    Args:
        query: Search query
        domain: Optional domain filter (국민연금, 건강보험, 복지로, 국세청)
        top_k: Number of results
        collection_name: Vector store collection name
        
    Returns:
        List of search results with action guides
    """
    vector_store = VectorStore(collection_name=collection_name)
    
    filter_metadata = None
    if domain:
        filter_metadata = {"domain": domain}
    
    results = vector_store.search(query, n_results=top_k, filter_metadata=filter_metadata)
    
    # Parse action_guide from JSON string
    for r in results:
        if r.get("metadata", {}).get("action_guide"):
            try:
                r["metadata"]["action_guide"] = json.loads(r["metadata"]["action_guide"])
            except:
                pass
    
    return results


if __name__ == "__main__":
    print("Loading knowledge base...")
    count = load_knowledge_base()
    print(f"Total items: {count}")
    print(f"Stats: {check_knowledge_base()}")
    
    print("\nContact info:")
    contacts = get_all_contacts()
    for name, info in contacts.items():
        print(f"  {name}: {info.get('phone', 'N/A')}")

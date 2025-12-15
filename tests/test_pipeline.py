"""
Test cases for Document Helper pipeline.
"""
import os
import sys
import pytest

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestDocumentClassifier:
    """Test cases for document classifier agent."""
    
    def test_classifier_initialization(self):
        """Test that classifier initializes correctly."""
        from agents import DocumentClassifier, DOCUMENT_TYPES
        
        classifier = DocumentClassifier()
        assert classifier is not None
        assert len(DOCUMENT_TYPES) > 0
    
    def test_keyword_matching(self):
        """Test keyword-based pre-classification."""
        from agents import DocumentClassifier
        
        classifier = DocumentClassifier()
        
        # Test health insurance keywords
        matches = classifier._keyword_match("건강보험료 납부 고지서")
        assert len(matches) > 0
        
        # Test pension keywords
        matches = classifier._keyword_match("국민연금공단 지급 안내")
        assert len(matches) > 0


class TestInfoExtractor:
    """Test cases for information extractor agent."""
    
    def test_regex_patterns(self):
        """Test regex pattern extraction."""
        from agents import InfoExtractor
        
        extractor = InfoExtractor()
        
        # Test amount extraction
        text = "납부금액: 150,000원"
        results = extractor._extract_with_rules(text)
        assert len(results["amounts"]) > 0
        
        # Test date extraction
        text = "납부기한: 2025-01-31"
        results = extractor._extract_with_rules(text)
        assert len(results["dates"]) > 0
        
        # Test phone extraction
        text = "문의: 1577-1000"
        results = extractor._extract_with_rules(text)
        assert len(results["phones"]) > 0


class TestPipeline:
    """Test cases for analysis pipeline."""
    
    def test_pipeline_initialization(self):
        """Test that pipeline initializes correctly."""
        from core import DocumentAnalysisPipeline
        
        pipeline = DocumentAnalysisPipeline()
        assert pipeline is not None
        assert pipeline.classifier is not None
        assert pipeline.extractor is not None
        assert pipeline.planner is not None
        assert pipeline.simplifier is not None


class TestVectorStore:
    """Test cases for vector store."""
    
    def test_vector_store_initialization(self):
        """Test vector store initialization."""
        from rag import VectorStore
        
        store = VectorStore(collection_name="test_collection")
        assert store is not None
        
        stats = store.get_stats()
        assert "collection_name" in stats


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

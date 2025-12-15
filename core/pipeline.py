"""
Document Analysis Pipeline

Orchestrates the entire document analysis workflow.
"""
import os
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from core.preprocessor import DocumentPreprocessor, PreprocessedImage
from core.ocr_engine import OCREngine, OCRResult
from agents import (
    DocumentClassifier,
    InfoExtractor,
    RAGAgent,
    ActionPlanner,
    Simplifier
)


@dataclass
class AnalysisResult:
    """Complete document analysis result."""
    # Document info
    doc_type: str = ""
    doc_type_name: str = ""
    organization: str = ""
    
    # Risk assessment
    risk_level: str = "LOW"
    action_required: bool = False
    
    # Extracted info
    key_info: Dict[str, Any] = field(default_factory=dict)
    
    # Simplified content
    summary_one_line: str = ""
    what_is_this: str = ""
    key_points: List[str] = field(default_factory=list)
    steps_easy: List[str] = field(default_factory=list)
    dont_worry: str = ""
    need_help_message: str = ""
    
    # Action plan
    action_plan: Dict[str, Any] = field(default_factory=dict)
    
    # Evidence
    evidence_chunks: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    ocr_confidence: float = 0.0
    processing_time_ms: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "doc_type": self.doc_type,
            "doc_type_name": self.doc_type_name,
            "organization": self.organization,
            "risk_level": self.risk_level,
            "action_required": self.action_required,
            "summary_one_line": self.summary_one_line,
            "key_info": self.key_info,
            "what_is_this": self.what_is_this,
            "key_points": self.key_points,
            "steps_easy": self.steps_easy,
            "action_plan": self.action_plan,
            "dont_worry": self.dont_worry,
            "need_help_message": self.need_help_message,
            "evidence_chunks": self.evidence_chunks,
            "ocr_confidence": self.ocr_confidence,
            "processing_time_ms": self.processing_time_ms
        }


class DocumentAnalysisPipeline:
    """
    Orchestrates the complete document analysis pipeline.
    
    Pipeline stages:
    1. Preprocessing (image/PDF handling)
    2. OCR (text extraction)
    3. Document Classification
    4. Information Extraction
    5. RAG Context Retrieval
    6. Action Planning
    7. Simplification
    """
    
    def __init__(self):
        """Initialize all pipeline components."""
        self.preprocessor = DocumentPreprocessor()
        self.ocr_engine = OCREngine()
        self.classifier = DocumentClassifier()
        self.extractor = InfoExtractor()
        self.rag_agent = RAGAgent()
        self.planner = ActionPlanner()
        self.simplifier = Simplifier()
    
    def analyze(self, file_path: str) -> AnalysisResult:
        """
        Analyze a document file.
        
        Args:
            file_path: Path to the document (image or PDF)
            
        Returns:
            Complete analysis result
        """
        start_time = time.time()
        result = AnalysisResult()
        
        try:
            # Stage 1: Preprocess
            preprocessed_images = self.preprocessor.preprocess_file(file_path)
            
            # Stage 2: OCR
            ocr_results = []
            for img_data in preprocessed_images:
                ocr_result = self.ocr_engine.extract_from_pil_image(img_data.image)
                ocr_results.append(ocr_result)
            
            # Combine OCR text from all pages
            full_text = "\n\n".join([r.text for r in ocr_results])
            avg_confidence = sum([r.confidence for r in ocr_results]) / len(ocr_results) if ocr_results else 0
            
            result.ocr_confidence = avg_confidence
            
            if not full_text.strip():
                result.summary_one_line = "문서를 읽을 수 없습니다."
                result.what_is_this = "이미지 품질이 좋지 않아 글자를 인식하지 못했습니다."
                result.steps_easy = ["더 선명한 사진을 다시 찍어주세요."]
                return result
            
            # Stage 3: Document Classification
            classification = self.classifier.process(ocr_text=full_text)
            result.doc_type = classification.get("doc_type", "기타_공공문서")
            result.doc_type_name = classification.get("doc_type_name", "기타 공공문서")
            result.organization = classification.get("organization", "")
            
            # Stage 4: Information Extraction
            key_info = self.extractor.process(
                ocr_text=full_text,
                doc_type=result.doc_type
            )
            result.key_info = key_info
            result.action_required = key_info.get("action_required", False)
            
            # Determine risk level
            penalty_risk = key_info.get("penalty_risk", "NONE")
            if penalty_risk == "HIGH":
                result.risk_level = "HIGH"
            elif penalty_risk == "MEDIUM":
                result.risk_level = "MEDIUM"
            else:
                result.risk_level = "LOW"
            
            # Stage 5: RAG Context Retrieval
            rag_result = self.rag_agent.process(
                doc_type=result.doc_type,
                key_info=key_info,
                ocr_text=full_text
            )
            result.evidence_chunks = rag_result.get("retrieved_chunks", [])
            
            # Stage 6: Action Planning
            action_plan = self.planner.process(
                doc_type=result.doc_type,
                key_info=key_info,
                rag_context=rag_result
            )
            result.action_plan = action_plan
            
            # Stage 7: Simplification
            simplified = self.simplifier.process(
                doc_type=result.doc_type_name,
                key_info=key_info,
                action_plan=action_plan,
                rag_context=rag_result
            )
            
            result.summary_one_line = simplified.get("summary_one_line", "")
            result.what_is_this = simplified.get("what_is_this", "")
            result.key_points = simplified.get("key_points", [])
            result.steps_easy = simplified.get("steps_easy", [])
            result.risk_level = simplified.get("risk_level", result.risk_level)
            result.dont_worry = simplified.get("dont_worry", "")
            result.need_help_message = simplified.get("need_help_message", "")
            
        except Exception as e:
            result.summary_one_line = "문서 분석 중 오류가 발생했습니다."
            result.what_is_this = f"오류: {str(e)}"
            result.steps_easy = ["다시 시도해주세요."]
        
        finally:
            elapsed = (time.time() - start_time) * 1000
            result.processing_time_ms = int(elapsed)
        
        return result
    
    def analyze_text(self, text: str) -> AnalysisResult:
        """
        Analyze pre-extracted text (skip OCR).
        
        Args:
            text: Document text
            
        Returns:
            Analysis result
        """
        start_time = time.time()
        result = AnalysisResult()
        result.ocr_confidence = 100.0  # Perfect since text is provided
        
        try:
            # Skip to Stage 3: Classification
            classification = self.classifier.process(ocr_text=text)
            result.doc_type = classification.get("doc_type", "기타_공공문서")
            result.doc_type_name = classification.get("doc_type_name", "기타 공공문서")
            result.organization = classification.get("organization", "")
            
            # Stage 4: Information Extraction
            key_info = self.extractor.process(
                ocr_text=text,
                doc_type=result.doc_type
            )
            result.key_info = key_info
            result.action_required = key_info.get("action_required", False)
            
            penalty_risk = key_info.get("penalty_risk", "NONE")
            if penalty_risk == "HIGH":
                result.risk_level = "HIGH"
            elif penalty_risk == "MEDIUM":
                result.risk_level = "MEDIUM"
            else:
                result.risk_level = "LOW"
            
            # Stage 5: RAG
            rag_result = self.rag_agent.process(
                doc_type=result.doc_type,
                key_info=key_info,
                ocr_text=text
            )
            result.evidence_chunks = rag_result.get("retrieved_chunks", [])
            
            # Stage 6: Action Planning
            action_plan = self.planner.process(
                doc_type=result.doc_type,
                key_info=key_info,
                rag_context=rag_result
            )
            result.action_plan = action_plan
            
            # Stage 7: Simplification
            simplified = self.simplifier.process(
                doc_type=result.doc_type_name,
                key_info=key_info,
                action_plan=action_plan,
                rag_context=rag_result
            )
            
            result.summary_one_line = simplified.get("summary_one_line", "")
            result.what_is_this = simplified.get("what_is_this", "")
            result.key_points = simplified.get("key_points", [])
            result.steps_easy = simplified.get("steps_easy", [])
            result.risk_level = simplified.get("risk_level", result.risk_level)
            result.dont_worry = simplified.get("dont_worry", "")
            result.need_help_message = simplified.get("need_help_message", "")
            
        except Exception as e:
            result.summary_one_line = "문서 분석 중 오류가 발생했습니다."
            result.what_is_this = f"오류: {str(e)}"
            result.steps_easy = ["다시 시도해주세요."]
        
        finally:
            elapsed = (time.time() - start_time) * 1000
            result.processing_time_ms = int(elapsed)
        
        return result

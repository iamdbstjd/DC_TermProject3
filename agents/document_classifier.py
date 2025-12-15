"""
Document Classifier Agent

Classifies public documents into specific types.
"""
import os
from typing import Dict, Any, List

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_agent import BaseAgent


# Known document types for Korean public documents
DOCUMENT_TYPES = {
    "건강보험료_고지서": {
        "keywords": ["건강보험", "보험료", "납부", "국민건강보험공단"],
        "description": "건강보험료 납부 고지서"
    },
    "국민연금_안내문": {
        "keywords": ["국민연금", "연금공단", "수급", "지급"],
        "description": "국민연금 관련 안내문"
    },
    "세금_통지서": {
        "keywords": ["국세청", "세금", "소득세", "부가가치세", "종합소득", "체납"],
        "description": "세금 관련 통지서"
    },
    "지방세_고지서": {
        "keywords": ["지방세", "재산세", "자동차세", "주민세"],
        "description": "지방세 관련 고지서"
    },
    "주민센터_안내문": {
        "keywords": ["주민센터", "동사무소", "행정복지센터", "민원"],
        "description": "주민센터/행정복지센터 안내문"
    },
    "복지_안내문": {
        "keywords": ["복지", "수급", "기초생활", "차상위", "지원금"],
        "description": "복지 관련 안내문"
    },
    "공과금_고지서": {
        "keywords": ["전기요금", "가스요금", "수도요금", "관리비", "아파트"],
        "description": "공과금/관리비 고지서"
    },
    "은행_통지서": {
        "keywords": ["은행", "대출", "이자", "예금", "적금", "카드"],
        "description": "금융기관 통지서"
    },
    "법원_통지서": {
        "keywords": ["법원", "소송", "재판", "출석", "판결"],
        "description": "법원 관련 통지서"
    },
    "기타_공공문서": {
        "keywords": [],
        "description": "기타 공공문서"
    }
}


class DocumentClassifier(BaseAgent):
    """
    Agent for classifying public documents into specific types.
    Uses keyword matching + LLM for accurate classification.
    """
    
    def __init__(self):
        super().__init__()
        self.document_types = DOCUMENT_TYPES
    
    def process(self, ocr_text: str, **kwargs) -> Dict[str, Any]:
        """
        Classify document based on OCR text.
        
        Args:
            ocr_text: Full text extracted from document via OCR
            
        Returns:
            Classification result with doc_type and confidence
        """
        # Step 1: Quick keyword-based pre-classification
        keyword_matches = self._keyword_match(ocr_text)
        
        # Step 2: LLM-based classification
        llm_result = self._llm_classify(ocr_text, keyword_matches)
        
        return llm_result
    
    def _keyword_match(self, text: str) -> List[str]:
        """Find document types that match keywords in text."""
        text_lower = text.lower()
        matches = []
        
        for doc_type, info in self.document_types.items():
            for keyword in info["keywords"]:
                if keyword in text_lower:
                    matches.append(doc_type)
                    break
        
        return matches
    
    def _llm_classify(self, ocr_text: str, keyword_matches: List[str]) -> Dict[str, Any]:
        """Use LLM to classify document."""
        
        doc_types_list = "\n".join([
            f"- {key}: {info['description']}"
            for key, info in self.document_types.items()
        ])
        
        system_prompt = """당신은 한국 공공문서 분류 전문가입니다.
주어진 문서 텍스트를 분석하여 문서 종류를 정확히 분류해주세요.

다음 JSON 형식으로만 응답하세요:
{
    "doc_type": "문서 유형 코드",
    "doc_type_name": "문서 유형 이름 (한글)",
    "confidence": 0.0~1.0 사이의 확신도,
    "organization": "발송 기관명 (알 수 있다면)",
    "reasoning": "분류 근거 간단 설명"
}"""

        hint = ""
        if keyword_matches:
            hint = f"\n\n키워드 분석 결과 가능한 유형: {', '.join(keyword_matches)}"

        user_prompt = f"""다음 문서를 분류해주세요.

사용 가능한 문서 유형:
{doc_types_list}

=== 문서 텍스트 (OCR 추출) ===
{ocr_text[:3000]}
==={hint}"""

        result = self._call_llm_json(system_prompt, user_prompt)
        
        # Ensure required fields exist
        if "doc_type" not in result:
            result["doc_type"] = "기타_공공문서"
        if "doc_type_name" not in result:
            result["doc_type_name"] = "기타 공공문서"
        if "confidence" not in result:
            result["confidence"] = 0.5
        if "organization" not in result:
            result["organization"] = "알 수 없음"
        
        return result

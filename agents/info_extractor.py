"""
Information Extractor Agent

Extracts key information from public documents.
Uses regex + LLM hybrid approach for accurate extraction.
"""
import os
import re
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_agent import BaseAgent


@dataclass
class ExtractedInfo:
    """Represents extracted key information from a document."""
    amount: Optional[str] = None  # 금액
    due_date: Optional[str] = None  # 납부/마감 기한
    organization: Optional[str] = None  # 발송 기관
    penalty_risk: str = "NONE"  # NONE, LOW, MEDIUM, HIGH
    action_required: bool = False  # 즉시 조치 필요 여부
    contact: Optional[str] = None  # 연락처
    account_number: Optional[str] = None  # 계좌번호/납부번호
    recipient_name: Optional[str] = None  # 수신인 이름
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "amount": self.amount,
            "due_date": self.due_date,
            "organization": self.organization,
            "penalty_risk": self.penalty_risk,
            "action_required": self.action_required,
            "contact": self.contact,
            "account_number": self.account_number,
            "recipient_name": self.recipient_name
        }


class InfoExtractor(BaseAgent):
    """
    Agent for extracting key information from public documents.
    Uses rule-based extraction + LLM refinement.
    """
    
    def __init__(self):
        super().__init__()
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for common information types."""
        # Korean currency amounts
        self.amount_patterns = [
            re.compile(r'(\d{1,3}(?:,\d{3})*)\s*원'),
            re.compile(r'₩\s*(\d{1,3}(?:,\d{3})*)'),
            re.compile(r'금\s*(\d{1,3}(?:,\d{3})*)\s*원'),
            re.compile(r'합계[:\s]*(\d{1,3}(?:,\d{3})*)\s*원'),
            re.compile(r'총액[:\s]*(\d{1,3}(?:,\d{3})*)\s*원'),
            re.compile(r'납부금액[:\s]*(\d{1,3}(?:,\d{3})*)\s*원'),
        ]
        
        # Date patterns
        self.date_patterns = [
            re.compile(r'(\d{4})[-./년]\s*(\d{1,2})[-./월]\s*(\d{1,2})일?'),
            re.compile(r'(\d{4})\.(\d{2})\.(\d{2})'),
            re.compile(r'납부기한[:\s]*(\d{4}[-./]\d{1,2}[-./]\d{1,2})'),
            re.compile(r'마감일[:\s]*(\d{4}[-./]\d{1,2}[-./]\d{1,2})'),
            re.compile(r'기한[:\s]*(\d{4}[-./]\d{1,2}[-./]\d{1,2})'),
        ]
        
        # Phone number patterns
        self.phone_patterns = [
            re.compile(r'(\d{2,4})[-)\s](\d{3,4})[-\s](\d{4})'),
            re.compile(r'(1\d{3})'),  # Special numbers like 1355, 1588
            re.compile(r'전화[:\s]*([\d\-]+)'),
            re.compile(r'연락처[:\s]*([\d\-]+)'),
            re.compile(r'문의[:\s]*([\d\-]+)'),
        ]
        
        # Account number patterns
        self.account_patterns = [
            re.compile(r'계좌[^\d]*(\d{2,4}[-\s]?\d{2,6}[-\s]?\d{2,6})'),
            re.compile(r'납부번호[:\s]*([\d\-]+)'),
            re.compile(r'가상계좌[:\s]*([\d\-]+)'),
        ]
    
    def process(
        self, 
        ocr_text: str, 
        doc_type: str = "",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Extract key information from document text.
        
        Args:
            ocr_text: Full text extracted from document
            doc_type: Document type from classifier
            
        Returns:
            Extracted information dict
        """
        # Step 1: Rule-based extraction
        rule_based = self._extract_with_rules(ocr_text)
        
        # Step 2: LLM refinement and additional extraction
        llm_result = self._extract_with_llm(ocr_text, doc_type, rule_based)
        
        return llm_result
    
    def _extract_with_rules(self, text: str) -> Dict[str, List[str]]:
        """Extract candidates using regex patterns."""
        results = {
            "amounts": [],
            "dates": [],
            "phones": [],
            "accounts": []
        }
        
        # Extract amounts
        for pattern in self.amount_patterns:
            for match in pattern.finditer(text):
                amount = match.group(0)
                if amount not in results["amounts"]:
                    results["amounts"].append(amount)
        
        # Extract dates
        for pattern in self.date_patterns:
            for match in pattern.finditer(text):
                date = match.group(0)
                if date not in results["dates"]:
                    results["dates"].append(date)
        
        # Extract phone numbers
        for pattern in self.phone_patterns:
            for match in pattern.finditer(text):
                phone = match.group(0)
                if phone not in results["phones"]:
                    results["phones"].append(phone)
        
        # Extract account numbers
        for pattern in self.account_patterns:
            for match in pattern.finditer(text):
                account = match.group(1) if match.lastindex else match.group(0)
                if account not in results["accounts"]:
                    results["accounts"].append(account)
        
        return results
    
    def _extract_with_llm(
        self, 
        ocr_text: str, 
        doc_type: str,
        rule_candidates: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Use LLM to refine and select correct information."""
        
        candidates_str = ""
        if rule_candidates["amounts"]:
            candidates_str += f"금액 후보: {', '.join(rule_candidates['amounts'][:5])}\n"
        if rule_candidates["dates"]:
            candidates_str += f"날짜 후보: {', '.join(rule_candidates['dates'][:5])}\n"
        if rule_candidates["phones"]:
            candidates_str += f"연락처 후보: {', '.join(rule_candidates['phones'][:5])}\n"
        if rule_candidates["accounts"]:
            candidates_str += f"계좌/납부번호 후보: {', '.join(rule_candidates['accounts'][:3])}\n"
        
        system_prompt = """당신은 한국 공공문서 정보 추출 전문가입니다.
문서에서 핵심 정보를 정확하게 추출해주세요.

⚠️ 긴급 키워드 감지 우선:
다음 키워드가 포함되어 있으면 반드시 penalty_risk를 HIGH 또는 MEDIUM으로, action_required를 true로 설정하세요:
- 독촉, 독촉장, 최고장 → HIGH
- 체납, 연체, 미납 → HIGH
- 압류, 압류 예고 → HIGH
- 독촉(이)왔어, 독촉(이)왔다 → HIGH
- 과태료, 가산금 → MEDIUM
- 납부 기한 경과, 기한 초과 → MEDIUM

다음 JSON 형식으로만 응답하세요:
{
    "amount": "납부해야 할 금액 (원 단위, 없으면 null)",
    "due_date": "납부/마감 기한 (YYYY-MM-DD 형식, 없으면 null)",
    "organization": "문서를 보낸 기관명",
    "penalty_risk": "불이익/연체료 위험 (NONE/LOW/MEDIUM/HIGH)",
    "action_required": true/false (즉시 조치가 필요한지),
    "contact": "문의 연락처",
    "account_number": "납부 계좌번호 또는 납부번호",
    "recipient_name": "수신인 이름 (있다면)",
    "urgency_keywords_found": ["발견된 긴급 키워드들"],
    "reasoning": "추출 근거 간단 설명"
}

penalty_risk 기준:
- NONE: 안내문으로 불이익 없음
- LOW: 기한 넘겨도 큰 불이익 없음
- MEDIUM: 연체료/과태료 발생 가능
- HIGH: 독촉장/체납/압류 등 즉시 조치 필요, 법적 조치 가능"""

        user_prompt = f"""다음 문서에서 핵심 정보를 추출해주세요.

문서 유형: {doc_type if doc_type else "미확인"}

=== 추출된 후보 정보 ===
{candidates_str if candidates_str else "없음"}

=== 문서 텍스트 ===
{ocr_text[:4000]}"""

        result = self._call_llm_json(system_prompt, user_prompt)
        
        # Ensure all fields exist with defaults
        defaults = {
            "amount": None,
            "due_date": None,
            "organization": None,
            "penalty_risk": "NONE",
            "action_required": False,
            "contact": None,
            "account_number": None,
            "recipient_name": None
        }
        
        for key, default in defaults.items():
            if key not in result:
                result[key] = default
        
        return result

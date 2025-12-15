"""
Action Planner Agent

Generates action plans based on document analysis.
"""
import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_agent import BaseAgent


class ActionType(str, Enum):
    """Types of actions user might need to take."""
    NONE = "NONE"       # 할 일 없음 (안내문)
    PAY = "PAY"         # 납부 필요
    CALL = "CALL"       # 전화 문의 필요
    VISIT = "VISIT"     # 방문 필요
    CHECK = "CHECK"     # 추가 확인 필요
    SUBMIT = "SUBMIT"   # 서류 제출 필요
    URGENT = "URGENT"   # 긴급 조치 필요


@dataclass
class ActionPlan:
    """Represents an action plan for the user."""
    action_type: ActionType
    steps: List[str]
    urgency: str  # LOW, MEDIUM, HIGH
    deadline_info: Optional[str] = None
    contact_info: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_type": self.action_type.value,
            "steps": self.steps,
            "urgency": self.urgency,
            "deadline_info": self.deadline_info,
            "contact_info": self.contact_info
        }


class ActionPlanner(BaseAgent):
    """
    Agent for generating action plans based on document analysis.
    Creates step-by-step instructions for users.
    """
    
    def __init__(self):
        super().__init__()
    
    def process(
        self,
        doc_type: str,
        key_info: Dict[str, Any],
        rag_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate action plan based on document analysis.
        
        Args:
            doc_type: Classified document type
            key_info: Extracted key information
            rag_context: Retrieved context from knowledge base
            
        Returns:
            Action plan with steps
        """
        # Determine action type and urgency
        action_type = self._determine_action_type(doc_type, key_info)
        urgency = self._determine_urgency(key_info)
        
        # Generate steps using LLM
        result = self._generate_action_plan(
            doc_type, 
            key_info, 
            action_type, 
            urgency,
            rag_context
        )
        
        return result
    
    def _determine_action_type(
        self, 
        doc_type: str, 
        key_info: Dict[str, Any]
    ) -> ActionType:
        """Determine the type of action required."""
        
        # Check for payment requirements
        if key_info.get("amount") and key_info.get("due_date"):
            if key_info.get("penalty_risk") == "HIGH":
                return ActionType.URGENT
            return ActionType.PAY
        
        # Check if action is explicitly required
        if key_info.get("action_required"):
            if key_info.get("penalty_risk") == "HIGH":
                return ActionType.URGENT
            return ActionType.CHECK
        
        # Document type specific logic
        doc_type_lower = doc_type.lower()
        
        if "고지서" in doc_type_lower or "납부" in doc_type_lower:
            if key_info.get("amount"):
                return ActionType.PAY
        
        if "통지서" in doc_type_lower or "체납" in doc_type_lower:
            return ActionType.URGENT
        
        if "안내문" in doc_type_lower:
            return ActionType.NONE
        
        return ActionType.CHECK
    
    def _determine_urgency(self, key_info: Dict[str, Any]) -> str:
        """Determine urgency level."""
        penalty_risk = key_info.get("penalty_risk", "NONE")
        
        if penalty_risk == "HIGH":
            return "HIGH"
        elif penalty_risk == "MEDIUM":
            return "MEDIUM"
        elif key_info.get("action_required"):
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_action_plan(
        self,
        doc_type: str,
        key_info: Dict[str, Any],
        action_type: ActionType,
        urgency: str,
        rag_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate detailed action plan using LLM."""
        
        context_str = ""
        if rag_context and rag_context.get("summary"):
            context_str = f"\n참고 정보: {rag_context['summary']}"
        
        system_prompt = """당신은 디지털 취약계층을 돕는 친절한 안내원입니다.
공공문서를 받은 사용자가 무엇을 해야 하는지 단계별로 안내해주세요.

다음 JSON 형식으로만 응답하세요:
{
    "action_type": "행동 유형 (NONE/PAY/CALL/VISIT/CHECK/SUBMIT/URGENT)",
    "urgency": "긴급도 (LOW/MEDIUM/HIGH)",
    "steps": [
        "1단계: 구체적인 행동 설명",
        "2단계: 다음 행동",
        ...
    ],
    "deadline_info": "기한 정보 (있다면)",
    "contact_info": "문의처 정보 (있다면)",
    "what_if_ignore": "이 문서를 무시하면 어떻게 되는지"
}

중요 원칙:
1. 초등학생도 이해할 수 있는 쉬운 말 사용
2. 각 단계는 하나의 행동만 포함
3. 구체적인 장소, 전화번호, 시간 포함
4. 불필요한 걱정을 주지 않으면서도 중요한 정보는 명확히"""

        action_desc = {
            ActionType.NONE: "특별히 할 일 없음 (안내문)",
            ActionType.PAY: "돈을 내야 함",
            ActionType.CALL: "전화해서 확인/문의 필요",
            ActionType.VISIT: "직접 방문 필요",
            ActionType.CHECK: "추가 확인 필요",
            ActionType.SUBMIT: "서류 제출 필요",
            ActionType.URGENT: "긴급하게 처리 필요"
        }

        user_prompt = f"""문서 유형: {doc_type}
예상 행동 유형: {action_desc.get(action_type, "확인 필요")}
긴급도: {urgency}

핵심 정보:
- 금액: {key_info.get('amount', '없음')}
- 기한: {key_info.get('due_date', '없음')}
- 발송 기관: {key_info.get('organization', '알 수 없음')}
- 불이익 위험: {key_info.get('penalty_risk', 'NONE')}
- 연락처: {key_info.get('contact', '없음')}
{context_str}

이 문서를 받은 사람이 무엇을 해야 하는지 단계별로 안내해주세요."""

        result = self._call_llm_json(system_prompt, user_prompt)
        
        # Ensure required fields
        if "steps" not in result or not result["steps"]:
            result["steps"] = ["이 문서에 대해 추가 확인이 필요합니다."]
        
        if "action_type" not in result:
            result["action_type"] = action_type.value
        
        if "urgency" not in result:
            result["urgency"] = urgency
        
        return result

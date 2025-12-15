"""
Simplifier Agent Module

Rewrites complex text in simple, easy-to-understand Korean.
Optimized for digitally vulnerable populations.
"""
import os
from typing import Dict, Any, List, Optional

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .base_agent import BaseAgent


class Simplifier(BaseAgent):
    """
    Agent for rewriting information in simple, accessible Korean.
    Targets: elderly, low digital literacy users.
    """
    
    def __init__(self):
        super().__init__()
    
    def process(
        self,
        doc_type: str,
        key_info: Dict[str, Any],
        action_plan: Dict[str, Any],
        rag_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Simplify all information for easy understanding.
        
        Args:
            doc_type: Document type
            key_info: Extracted key information
            action_plan: Generated action plan
            rag_context: Retrieved context
            
        Returns:
            Simplified explanation and steps
        """
        result = self._generate_simple_explanation(
            doc_type,
            key_info,
            action_plan,
            rag_context
        )
        
        return result
    
    def _generate_simple_explanation(
        self,
        doc_type: str,
        key_info: Dict[str, Any],
        action_plan: Dict[str, Any],
        rag_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate simplified explanation using LLM."""
        
        # Extract action guide from RAG context if available
        action_guide_info = ""
        if rag_context and rag_context.get("retrieved_chunks"):
            for chunk in rag_context["retrieved_chunks"]:
                metadata = chunk.get("metadata", {})
                if metadata.get("action_guide"):
                    guide = metadata["action_guide"]
                    if isinstance(guide, str):
                        import json
                        try:
                            guide = json.loads(guide)
                        except:
                            guide = {}
                    
                    if guide.get("phone"):
                        phone = guide["phone"]
                        action_guide_info += f"\n📞 전화: {phone.get('number', '')} ({phone.get('hours', '')})"
                        if phone.get("script"):
                            action_guide_info += f" - '{phone['script']}' 라고 말하세요"
                    if guide.get("online"):
                        online = guide["online"]
                        action_guide_info += f"\n🌐 인터넷: {online.get('url', '')}"
                        if online.get("app"):
                            action_guide_info += f" (앱: {online['app']})"
                    if guide.get("visit"):
                        visit = guide["visit"]
                        action_guide_info += f"\n🏢 방문: {visit.get('place', '')}"
                        if visit.get("documents"):
                            action_guide_info += f" (준비물: {', '.join(visit['documents'])})"
                    break  # Use first matching action guide
        
        system_prompt = """당신은 어르신과 디지털에 익숙하지 않은 분들을 위한 친절한 안내원입니다.

공공문서 내용을 최대한 쉽고 간단하게 설명해주세요.

⚠️ 중요 원칙:
- penalty_risk가 HIGH이면: "안심하세요" 라고 하지 마세요! 대신 빨리 조치해야 한다고 알려주세요.
- 독촉, 체납, 연체, 미납 키워드가 있으면: 심각한 상황임을 명확히 전달하세요.
- risk_level은 반드시 입력된 penalty_risk와 동일하게 설정하세요.

작성 원칙:
1. 초등학교 3학년도 이해할 수 있는 말 사용
2. 한 문장은 15자 이내로 짧게
3. 어려운 한자어나 영어 사용 금지
4. 숫자와 날짜는 크고 명확하게
5. 가장 중요한 것(할 일 있음/없음)을 맨 처음에
6. HIGH 위험이면 걱정해야 한다고 명확히 알려주세요!
7. 도움받는 3가지 방법(전화, 인터넷, 방문)을 항상 안내

다음 JSON 형식으로만 응답하세요:
{
    "summary_one_line": "한 줄 핵심 결론 (20자 이내)",
    "risk_level": "LOW/MEDIUM/HIGH",
    "risk_message": "위험도에 대한 쉬운 설명",
    "what_is_this": "이 문서가 무엇인지 쉬운 설명 (2-3문장)",
    "key_points": [
        "💰 금액 관련 쉬운 설명",
        "📅 기한 관련 쉬운 설명",
        "🏢 어디서 온 건지"
    ],
    "steps_easy": [
        "1️⃣ 첫 번째 할 일 (쉬운 말로)",
        "2️⃣ 두 번째 할 일",
        "3️⃣ 세 번째 할 일"
    ],
    "help_channels": {
        "phone": "📞 전화: 번호 + 뭐라고 말할지",
        "online": "🌐 인터넷: 주소 또는 앱 이름",
        "visit": "🏢 방문: 어디에 가서 뭘 가져가야 하는지"
    },
    "dont_worry": "안심 메시지 (필요한 경우)",
    "need_help_message": "도움이 필요하면 누구에게 물어볼지"
}"""

        # Prepare context
        steps = action_plan.get("steps", [])
        urgency = action_plan.get("urgency", "LOW")
        action_type = action_plan.get("action_type", "CHECK")
        
        user_prompt = f"""다음 정보를 쉽게 설명해주세요.

📄 문서 종류: {doc_type}

📋 핵심 정보:
- 내야 할 돈: {key_info.get('amount', '없음')}
- 마감 기한: {key_info.get('due_date', '없음')}
- 보낸 곳: {key_info.get('organization', '알 수 없음')}
- 연락처: {key_info.get('contact', '없음')}
- 위험도: {key_info.get('penalty_risk', 'NONE')}

🎯 해야 할 일:
- 행동 종류: {action_type}
- 긴급도: {urgency}
- 단계들: {steps}

🆘 도움받는 방법:{action_guide_info if action_guide_info else " 알 수 없음"}

위 내용을 어르신도 쉽게 이해할 수 있도록 다시 써주세요."""

        result = self._call_llm_json(system_prompt, user_prompt)
        
        # Ensure all required fields exist
        defaults = {
            "summary_one_line": "확인이 필요한 문서입니다.",
            "risk_level": "LOW",
            "risk_message": "",
            "what_is_this": "공공기관에서 보낸 문서입니다.",
            "key_points": [],
            "steps_easy": ["자세히 읽어보세요."],
            "help_channels": {},
            "dont_worry": "",
            "need_help_message": "가까운 주민센터에 문의하세요."
        }
        
        for key, default in defaults.items():
            if key not in result or not result[key]:
                result[key] = default
        
        return result
    
    def simplify_text(self, text: str) -> str:
        """Simplify a single text passage."""
        
        system_prompt = """어려운 공공문서 문장을 초등학생도 이해할 수 있게 바꿔주세요.
짧고 쉬운 말로 핵심만 남겨주세요."""

        return self._call_llm(system_prompt, text, max_tokens=200)

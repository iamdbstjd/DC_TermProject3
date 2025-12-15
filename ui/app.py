"""
Streamlit UI for Document Helper

User-friendly interface for analyzing public documents.
Designed for digitally vulnerable populations.
"""
import os
import sys
import requests
import streamlit as st
from PIL import Image
import io

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Page config
st.set_page_config(
    page_title="문서 도우미 📄",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Session state for font size
if 'font_size' not in st.session_state:
    st.session_state.font_size = 'medium'
if 'current_result' not in st.session_state:
    st.session_state.current_result = None
if 'show_more_detail' not in st.session_state:
    st.session_state.show_more_detail = False

# Font size configurations
FONT_SIZES = {
    'small': {'h1': '2rem', 'h2': '1.5rem', 'p': '1rem', 'step': '1.1rem'},
    'medium': {'h1': '2.5rem', 'h2': '1.8rem', 'p': '1.2rem', 'step': '1.3rem'},
    'large': {'h1': '3rem', 'h2': '2.2rem', 'p': '1.5rem', 'step': '1.6rem'},
    'xlarge': {'h1': '3.5rem', 'h2': '2.5rem', 'p': '1.8rem', 'step': '1.9rem'}
}

fs = FONT_SIZES[st.session_state.font_size]

# Custom CSS for accessibility
st.markdown(f"""
<style>
    /* Large, readable fonts */
    .main h1 {{
        font-size: {fs['h1']} !important;
        font-weight: bold !important;
        color: #1a1a1a !important;
        text-align: center;
        margin-bottom: 1rem;
    }}
    
    .main h2 {{
        font-size: {fs['h2']} !important;
        font-weight: 600 !important;
        color: #333 !important;
    }}
    
    .main h3 {{
        font-size: calc({fs['h2']} - 0.2rem) !important;
    }}
    
    .main p, .main li {{
        font-size: {fs['p']} !important;
        line-height: 1.8 !important;
    }}
    
    /* Summary card styles */
    .summary-card {{
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin: 1rem 0;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }}
    
    .summary-card h2 {{
        color: white !important;
        font-size: {fs['h2']} !important;
        margin-bottom: 0.5rem;
    }}
    
    .summary-card p {{
        font-size: {fs['step']} !important;
    }}
    
    /* Risk level badges */
    .risk-low {{
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 2rem;
        display: inline-block;
        font-weight: bold;
        font-size: {fs['p']};
    }}
    
    .risk-medium {{
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 2rem;
        display: inline-block;
        font-weight: bold;
        font-size: {fs['p']};
    }}
    
    .risk-high {{
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 2rem;
        display: inline-block;
        font-weight: bold;
        font-size: {fs['p']};
        animation: pulse 2s infinite;
    }}
    
    @keyframes pulse {{
        0% {{ transform: scale(1); }}
        50% {{ transform: scale(1.05); }}
        100% {{ transform: scale(1); }}
    }}
    
    /* Step cards */
    .step-card {{
        background: white;
        border: 2px solid #e0e0e0;
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 0.8rem 0;
        font-size: {fs['step']} !important;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        transition: transform 0.2s;
    }}
    
    .step-card:hover {{
        transform: translateX(5px);
        border-color: #667eea;
    }}
    
    /* Contact cards */
    .contact-card {{
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 1rem;
        padding: 1.5rem;
        margin: 0.5rem 0;
        font-size: {fs['p']};
    }}
    
    .contact-card .phone {{
        font-size: calc({fs['h2']} + 0.3rem);
        font-weight: bold;
        color: #4CAF50;
    }}
    
    /* Upload area */
    .uploadfile {{
        border: 3px dashed #667eea !important;
        border-radius: 1rem !important;
        padding: 2rem !important;
    }}
    
    /* Buttons */
    .stButton > button {{
        font-size: {fs['p']} !important;
        padding: 0.8rem 2rem !important;
        border-radius: 0.8rem !important;
    }}
    
    /* Don't worry section */
    .dont-worry {{
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        font-size: {fs['p']};
    }}
    
    /* History item */
    .history-item {{
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 0.5rem 0.5rem 0;
        cursor: pointer;
    }}
    
    .history-item:hover {{
        background: #e9ecef;
    }}
    
    /* Sidebar */
    .css-1d391kg {{
        font-size: {fs['p']} !important;
    }}
</style>
""", unsafe_allow_html=True)

# API endpoint
API_URL = os.environ.get("API_URL", "http://localhost:8001")

# Default contacts (fallback)
DEFAULT_CONTACTS = {
    "국민연금공단": {"phone": "1355", "website": "https://www.nps.or.kr", "hours": "평일 09:00-18:00"},
    "국민건강보험공단": {"phone": "1577-1000", "website": "https://www.nhis.or.kr", "hours": "평일 09:00-18:00"},
    "보건복지상담센터": {"phone": "129", "website": "https://www.bokjiro.go.kr", "hours": "24시간"},
    "국세상담센터": {"phone": "126", "website": "https://www.hometax.go.kr", "hours": "평일 09:00-18:00"}
}


def get_risk_badge(risk_level: str) -> str:
    """Generate HTML for risk level badge."""
    risk_messages = {
        "LOW": ("✅ 안심하세요", "risk-low"),
        "MEDIUM": ("⚠️ 확인이 필요해요", "risk-medium"),
        "HIGH": ("🚨 중요한 문서예요", "risk-high")
    }
    message, css_class = risk_messages.get(risk_level, ("확인 필요", "risk-medium"))
    return f'<span class="{css_class}">{message}</span>'


def get_contacts():
    """Get contacts from API."""
    try:
        response = requests.get(f"{API_URL}/contacts", timeout=5)
        if response.status_code == 200:
            return response.json().get("contacts", DEFAULT_CONTACTS)
    except:
        pass
    return DEFAULT_CONTACTS


def get_history():
    """Get history from API."""
    try:
        response = requests.get(f"{API_URL}/history?limit=10", timeout=5)
        if response.status_code == 200:
            return response.json().get("history", [])
    except:
        pass
    return []


def display_contacts():
    """Display contact information."""
    contacts = get_contacts()
    
    st.markdown("### 📞 도움받을 수 있는 곳")
    
    for name, info in contacts.items():
        st.markdown(f"""
        <div class="contact-card">
            <strong>{name}</strong><br>
            <span class="phone">📞 {info.get('phone', '')}</span><br>
            🕐 {info.get('hours', '평일 09:00-18:00')}<br>
            🌐 {info.get('website', '')}
        </div>
        """, unsafe_allow_html=True)


def display_analysis_result(result: dict):
    """Display analysis result in user-friendly format."""
    
    # Summary section
    st.markdown(f"""
    <div class="summary-card">
        <h2>📋 한 줄 요약</h2>
        <p>{result.get('summary_one_line', '분석 결과를 확인하세요')}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Risk level
    risk_level = result.get('risk_level', 'LOW')
    st.markdown(f"""
    <div style="text-align: center; margin: 1.5rem 0;">
        {get_risk_badge(risk_level)}
    </div>
    """, unsafe_allow_html=True)
    
    # What is this document
    st.markdown("### 📄 이 문서는 무엇인가요?")
    st.markdown(f"**{result.get('doc_type_name', '공공문서')}**")
    st.markdown(result.get('what_is_this', ''))
    
    # Key information
    key_info = result.get('key_info', {})
    if key_info:
        st.markdown("### 💡 중요한 정보")
        
        col1, col2 = st.columns(2)
        
        with col1:
            amount = key_info.get('amount')
            if amount:
                st.metric("💰 금액", amount)
            
            org = key_info.get('organization')
            if org:
                st.metric("🏢 보낸 곳", org)
        
        with col2:
            due_date = key_info.get('due_date')
            if due_date:
                st.metric("📅 기한", due_date)
            
            contact = key_info.get('contact')
            if contact:
                st.metric("📞 연락처", contact)
    
    # Key points with emojis
    key_points = result.get('key_points', [])
    if key_points:
        st.markdown("### 📌 핵심 포인트")
        for point in key_points:
            st.markdown(f"""
            <div class="step-card">
                {point}
            </div>
            """, unsafe_allow_html=True)
    
    # Step-by-step guide
    steps = result.get('steps_easy', [])
    if steps:
        st.markdown("### ✅ 이렇게 하세요")
        for step in steps:
            st.markdown(f"""
            <div class="step-card">
                {step}
            </div>
            """, unsafe_allow_html=True)
    
    # SOS Section - 도움받는 곳
    st.markdown("### 🆘 도움이 필요하면 여기로 전화하세요")
    display_contacts()
    
    # Don't worry message
    dont_worry = result.get('dont_worry', '')
    if dont_worry:
        st.markdown(f"""
        <div class="dont-worry">
            💪 {dont_worry}
        </div>
        """, unsafe_allow_html=True)
    
    # Feedback buttons
    st.markdown("---")
    st.markdown("### 📝 이 설명이 도움이 되었나요?")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("😊 충분해요!", use_container_width=True, key="btn_helpful"):
            st.success("감사합니다!")
            st.session_state.current_result = None
            st.session_state.show_more_detail = False
            st.rerun()
    
    with col2:
        if st.button("😕 잘 모르겠어요", use_container_width=True, key="btn_confused"):
            st.session_state.show_more_detail = True
            st.rerun()
    
    # More detail section
    if st.session_state.show_more_detail:
        st.markdown("---")
        st.markdown("### 🔍 더 자세한 설명")
        st.info("""
        **이 문서가 어려우시다면:**
        
        1️⃣ 가족이나 주변 분께 이 화면을 보여주세요
        
        2️⃣ 아래 전화번호로 직접 전화해보세요:
        - 뭐든지 물어보세요: **129** (보건복지상담)
        - 연금 관련: **1355** (국민연금)
        - 건강보험 관련: **1577-1000** (건강보험)
        - 세금 관련: **126** (국세청)
        
        3️⃣ 가까운 **주민센터**를 방문하시면 직접 도와드립니다
        """)
        
        st.warning("💡 **전화할 때 이렇게 말하세요:** '우편물을 받았는데 무슨 내용인지 모르겠어요'")


def main():
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ 설정")
        
        # Font size control
        st.markdown("### 🔤 글씨 크기")
        font_option = st.radio(
            "글씨 크기 선택",
            options=['small', 'medium', 'large', 'xlarge'],
            format_func=lambda x: {'small': '작게', 'medium': '보통', 'large': '크게', 'xlarge': '아주 크게'}[x],
            index=['small', 'medium', 'large', 'xlarge'].index(st.session_state.font_size),
            key="font_selector"
        )
        if font_option != st.session_state.font_size:
            st.session_state.font_size = font_option
            st.rerun()
        
        st.markdown("---")
        
        # History section
        st.markdown("### 📜 이전 검색 기록")
        history = get_history()
        
        if history:
            for item in history[:5]:
                risk_emoji = {"LOW": "✅", "MEDIUM": "⚠️", "HIGH": "🚨"}.get(item.get("risk_level", "LOW"), "📄")
                if st.button(
                    f"{risk_emoji} {item.get('doc_type_name', '문서')[:10]}...",
                    key=f"hist_{item['id']}",
                    use_container_width=True
                ):
                    try:
                        response = requests.get(f"{API_URL}/history/{item['id']}", timeout=10)
                        if response.status_code == 200:
                            result_data = response.json()
                            if result_data.get("status") == "success":
                                st.session_state.current_result = result_data
                                st.rerun()
                            else:
                                st.error("기록 형식 오류")
                        else:
                            st.error(f"서버 오류: {response.status_code}")
                    except requests.exceptions.ConnectionError:
                        st.error("서버 연결 불가")
                    except Exception as e:
                        st.error(f"오류: {str(e)[:30]}")
        else:
            st.caption("아직 검색 기록이 없습니다.")
        
        st.markdown("---")
        
        # Contacts in sidebar
        st.markdown("### 📞 긴급 연락처")
        st.markdown("""
        - 🏥 **129** (복지상담)
        - 🏦 **1355** (연금)
        - 💊 **1577-1000** (건강보험)
        - 💰 **126** (세금)
        """)
    
    # Main content
    st.markdown("# 📄 문서 도우미")
    st.markdown(f"""
    <p style="text-align: center; color: #666; font-size: {fs['p']};">
        공공문서를 쉽게 이해할 수 있도록 도와드려요
    </p>
    """, unsafe_allow_html=True)
    
    # Show result if exists
    if st.session_state.current_result:
        st.markdown("---")
        display_analysis_result(st.session_state.current_result)
        
        st.markdown("---")
        if st.button("🔄 새 문서 분석하기", use_container_width=True):
            st.session_state.current_result = None
            st.session_state.show_more_detail = False
            st.rerun()
        return
    
    st.markdown("---")
    
    # File upload section
    st.markdown("### 📤 문서를 올려주세요")
    st.markdown(f"""
    <p style="color: #666; font-size: {fs['p']};">
        스마트폰으로 찍은 사진이나 PDF 파일을 올려주세요.<br>
        건강보험료 고지서, 연금 안내문, 세금 통지서 등을 분석해드립니다.
    </p>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "파일 선택",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf'],
        help="이미지(PNG, JPG) 또는 PDF 파일을 올려주세요"
    )
    
    if uploaded_file is not None:
        # Show uploaded file
        if uploaded_file.type.startswith('image'):
            st.image(uploaded_file, caption="업로드된 문서", use_container_width=True)
        
        # Analyze button
        if st.button("🔍 문서 분석하기", use_container_width=True, type="primary"):
            with st.spinner("📝 문서를 분석하고 있어요... 잠시만 기다려주세요..."):
                try:
                    # Send to API
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    response = requests.post(f"{API_URL}/analyze_document", files=files, timeout=120)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if result.get("status") == "success":
                            st.session_state.current_result = result
                            st.rerun()
                        else:
                            st.error("분석에 실패했습니다. 다시 시도해주세요.")
                    else:
                        st.error(f"오류가 발생했습니다: {response.text}")
                        
                except requests.exceptions.ConnectionError:
                    st.error("⚠️ 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.")
                except Exception as e:
                    st.error(f"오류가 발생했습니다: {str(e)}")
    
    # Text input alternative
    st.markdown("---")
    with st.expander("📝 텍스트로 직접 입력하기"):
        text_input = st.text_area(
            "문서 내용을 여기에 붙여넣으세요",
            height=200,
            placeholder="문서의 내용을 복사해서 여기에 붙여넣어주세요..."
        )
        
        if st.button("텍스트 분석하기", key="analyze_text"):
            if text_input.strip():
                with st.spinner("분석 중..."):
                    try:
                        response = requests.post(
                            f"{API_URL}/analyze_text",
                            json={"text": text_input},
                            timeout=120
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result.get("status") == "success":
                                st.session_state.current_result = result
                                st.rerun()
                        else:
                            st.error(f"오류: {response.text}")
                            
                    except Exception as e:
                        st.error(f"오류: {str(e)}")
            else:
                st.warning("텍스트를 입력해주세요.")
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <p style="text-align: center; color: #888; font-size: calc({fs['p']} - 0.2rem);">
        ℹ️ 이 서비스는 AI가 문서를 분석합니다.<br>
        중요한 결정은 반드시 관련 기관에 직접 확인하세요.
    </p>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()

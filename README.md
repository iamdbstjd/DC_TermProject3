# 📄 문서 도우미 (Document Helper)

디지털 취약계층을 위한 공공문서 분석 시스템

## 🎯 프로젝트 개요

공공기관에서 발송하는 다양한 서류(건강보험료 고지서, 국민연금 안내문, 세금 통지서 등)를 이미지나 PDF로 업로드하면:
- 📋 문서 종류를 자동으로 파악
- 💰 핵심 정보(금액, 마감일, 기관)를 추출
- ✅ 지금 해야 할 일을 단계별로 안내
- 📝 초등학생도 이해할 수 있는 쉬운 말로 설명

## 🏗️ 시스템 아키텍처

```
사용자 → [Streamlit UI] → [FastAPI Backend] → [Analysis Pipeline]
                                                    ↓
                          ┌─────────────────────────┴─────────────────────────┐
                          ↓                         ↓                         ↓
                    [OCR Engine]          [Document Classifier]        [Info Extractor]
                          ↓                         ↓                         ↓
                    [RAG Agent]            [Action Planner]           [Simplifier]
                          ↓                         ↓                         ↓
                          └─────────────────────────┴─────────────────────────┘
                                                    ↓
                                            [분석 결과 반환]
```

### 5개 AI 에이전트
1. **Document Classifier**: 문서 종류 분류 (건강보험, 연금, 세금 등)
2. **Info Extractor**: 핵심 정보 추출 (정규표현식 + LLM 하이브리드)
3. **RAG Agent**: 관련 공공문서 정보 검색
4. **Action Planner**: 행동 계획 생성 (PAY, CALL, VISIT 등)
5. **Simplifier**: 쉬운 한국어로 재작성

## 📁 프로젝트 구조

```
doc_helper/
├── agents/                 # AI 에이전트
│   ├── base_agent.py
│   ├── document_classifier.py
│   ├── info_extractor.py
│   ├── rag_agent.py
│   ├── action_planner.py
│   └── simplifier.py
├── core/                   # 핵심 모듈
│   ├── ocr_engine.py
│   ├── preprocessor.py
│   └── pipeline.py
├── rag/                    # RAG 모듈
│   ├── embeddings.py
│   └── vector_store.py
├── api/                    # FastAPI 백엔드
│   └── main.py
├── ui/                     # Streamlit 프론트엔드
│   └── app.py
├── data/
│   ├── uploads/
│   ├── vectordb/
│   └── knowledge_base/
├── tests/
├── config/
├── .env
└── requirements.txt
```

## 🚀 설치 및 실행

### 1. 의존성 설치

```bash
cd doc_helper
pip install -r requirements.txt
```

### 2. 환경 설정

`.env` 파일에 OpenAI API 키 설정:
```
OPENAI_API_KEY=your-actual-api-key
```

### 3. 지식베이스 로드 (선택사항)

```bash
python -c "from data.knowledge_base.loader import load_knowledge_base; load_knowledge_base()"
```

### 4. 서버 실행

**백엔드 (FastAPI):**
```bash
cd doc_helper
uvicorn api.main:app --reload --port 8001
```

**프론트엔드 (Streamlit):**
```bash
cd doc_helper
streamlit run ui/app.py --server.port 8502
```

### 5. 접속

- API 문서: http://localhost:8001/docs
- 웹 UI: http://localhost:8502

## 📡 API 엔드포인트

| 메서드 | 경로 | 설명 |
|--------|------|------|
| POST | `/analyze_document` | 이미지/PDF 문서 분석 |
| POST | `/analyze_text` | 텍스트 직접 분석 |
| POST | `/feedback` | 사용자 피드백 제출 |
| GET | `/health` | 서버 상태 확인 |
| GET | `/knowledge/stats` | 지식베이스 통계 |

### 응답 구조 예시

```json
{
  "doc_type": "국민연금_안내문",
  "doc_type_name": "국민연금 지급 안내문",
  "risk_level": "LOW",
  "summary_one_line": "지금 할 일은 없습니다.",
  "key_info": {
    "amount": null,
    "due_date": null,
    "organization": "국민연금공단",
    "penalty_risk": "NONE"
  },
  "steps_easy": [
    "1️⃣ 이 편지는 안내용입니다",
    "2️⃣ 따로 하실 일은 없어요"
  ]
}
```

## 🧪 테스트

```bash
cd doc_helper
pytest tests/ -v
```

## 📝 지원 문서 유형

- 건강보험료 고지서
- 국민연금 안내문
- 세금 통지서 (국세/지방세)
- 복지 안내문
- 공과금 고지서
- 주민센터 안내문
- 기타 공공문서

## 🔧 기술 스택

- **Backend**: FastAPI, Python 3.9+
- **Frontend**: Streamlit
- **AI/ML**: OpenAI GPT-4o-mini, Embeddings
- **Vector DB**: ChromaDB
- **OCR**: Tesseract (pytesseract)
- **PDF**: PyMuPDF

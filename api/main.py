"""
FastAPI Backend for Document Helper System

Provides REST API endpoints for document analysis.
"""
import os
import sys
import shutil
import uuid
import json
from datetime import datetime
from typing import Optional, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import settings
from core import DocumentAnalysisPipeline, AnalysisResult


# Initialize FastAPI app
app = FastAPI(
    title="문서 도우미 API (Document Helper)",
    description="디지털 취약계층을 위한 공공문서 분석 API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize pipeline
pipeline = DocumentAnalysisPipeline()

# In-memory history storage (in production, use a database)
analysis_history: List[dict] = []
HISTORY_FILE = os.path.join(settings.upload_dir, "history.json")


def load_history():
    """Load history from file."""
    global analysis_history
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                analysis_history = json.load(f)
        except:
            analysis_history = []


def save_history():
    """Save history to file."""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(analysis_history[-50:], f, ensure_ascii=False, indent=2)  # Keep last 50
    except:
        pass


def add_to_history(result: dict, filename: str = None):
    """Add analysis result to history."""
    history_entry = {
        "id": result.get("analysis_id", str(uuid.uuid4())),
        "timestamp": datetime.now().isoformat(),
        "filename": filename or "텍스트 입력",
        "doc_type_name": result.get("doc_type_name", "알 수 없음"),
        "summary_one_line": result.get("summary_one_line", ""),
        "risk_level": result.get("risk_level", "LOW"),
        "result": result
    }
    analysis_history.insert(0, history_entry)  # Add to front
    save_history()


# Load history on startup
load_history()


class TextAnalysisRequest(BaseModel):
    """Request model for text-based analysis."""
    text: str


class FeedbackRequest(BaseModel):
    """Request model for user feedback."""
    analysis_id: str
    helpful: bool
    feedback_type: Optional[str] = None  # "too_hard", "helpful", "incorrect"
    comment: Optional[str] = None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": "문서 도우미 API (Document Helper)",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    return {
        "status": "healthy",
        "api_key_configured": bool(settings.openai_api_key and settings.openai_api_key != "your-openai-api-key-here"),
        "upload_dir": settings.upload_dir,
        "vectordb_dir": settings.vectordb_dir
    }


@app.post("/analyze_document")
async def analyze_document(file: UploadFile = File(...)):
    """
    Analyze an uploaded document (image or PDF).
    
    Returns easy-to-understand analysis with:
    - One-line summary
    - Key information
    - Step-by-step action guide
    """
    try:
        # Validate file type
        allowed_extensions = {'.pdf', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
        ext = os.path.splitext(file.filename)[1].lower()
        
        if ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"지원하지 않는 파일 형식입니다: {ext}. 지원 형식: {allowed_extensions}"
            )
        
        # Save file temporarily
        file_id = str(uuid.uuid4())
        file_path = os.path.join(settings.upload_dir, f"{file_id}{ext}")
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        try:
            # Analyze document
            result = pipeline.analyze(file_path)
            
            # Build response
            response_data = {
                "status": "success",
                "analysis_id": file_id,
                "filename": file.filename,
                **result.to_dict()
            }
            
            # Add to history
            add_to_history(response_data, file.filename)
            
            return JSONResponse(response_data)
            
        finally:
            # Cleanup uploaded file
            if os.path.exists(file_path):
                os.remove(file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze_text")
async def analyze_text(request: TextAnalysisRequest):
    """
    Analyze document text directly (skip OCR).
    Useful when text is already extracted.
    """
    try:
        if not request.text or len(request.text.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="텍스트가 너무 짧습니다. 최소 10자 이상 입력해주세요."
            )
        
        # Analyze text
        result = pipeline.analyze_text(request.text)
        
        response_data = {
            "status": "success",
            "analysis_id": str(uuid.uuid4()),
            **result.to_dict()
        }
        
        # Add to history
        add_to_history(response_data)
        
        return JSONResponse(response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest):
    """
    Submit user feedback about analysis quality.
    """
    return {
        "status": "success",
        "message": "피드백이 접수되었습니다. 감사합니다!",
        "analysis_id": request.analysis_id
    }


@app.get("/history")
async def get_history(limit: int = 10):
    """Get recent analysis history."""
    return {
        "status": "success",
        "count": len(analysis_history[:limit]),
        "history": [
            {
                "id": h["id"],
                "timestamp": h["timestamp"],
                "filename": h["filename"],
                "doc_type_name": h["doc_type_name"],
                "summary_one_line": h["summary_one_line"],
                "risk_level": h["risk_level"]
            }
            for h in analysis_history[:limit]
        ]
    }


@app.get("/history/{analysis_id}")
async def get_history_detail(analysis_id: str):
    """Get detailed result from history."""
    for h in analysis_history:
        if h["id"] == analysis_id:
            return {
                "status": "success",
                **h["result"]
            }
    raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")


@app.delete("/history")
async def clear_history():
    """Clear all history."""
    global analysis_history
    analysis_history = []
    save_history()
    return {"status": "success", "message": "기록이 삭제되었습니다."}


@app.get("/contacts")
async def get_contacts():
    """Get all contact information for public services."""
    try:
        from data.knowledge_base.loader import get_all_contacts
        contacts = get_all_contacts()
        return {
            "status": "success",
            "contacts": contacts
        }
    except Exception as e:
        # Fallback contacts
        return {
            "status": "success",
            "contacts": {
                "국민연금공단": {"phone": "1355", "website": "https://www.nps.or.kr"},
                "국민건강보험공단": {"phone": "1577-1000", "website": "https://www.nhis.or.kr"},
                "보건복지상담센터": {"phone": "129", "website": "https://www.bokjiro.go.kr"},
                "국세상담센터": {"phone": "126", "website": "https://www.hometax.go.kr"}
            }
        }


@app.get("/knowledge/stats")
async def get_knowledge_stats():
    """Get knowledge base statistics."""
    try:
        from rag import VectorStore
        vector_store = VectorStore(collection_name="doc_helper_knowledge")
        stats = vector_store.get_stats()
        return stats
    except Exception as e:
        return {"error": str(e), "count": 0}


@app.post("/knowledge/reload")
async def reload_knowledge_base():
    """Reload knowledge base from JSON file."""
    try:
        from data.knowledge_base.loader import load_knowledge_base
        count = load_knowledge_base()
        return {
            "status": "success",
            "items_loaded": count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Run with: uvicorn api.main:app --reload --port 8001
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)


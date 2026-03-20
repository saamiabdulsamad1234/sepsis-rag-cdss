from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import uvicorn
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.schemas import (
    ChatRequest, ChatResponse,
    AnalysisRequest, AnalysisResponse
)
from rag_engine.pipeline import RAGPipeline

app = FastAPI(
    title="Sepsis RAG API",
    description="Clinical decision support for sepsis prediction",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_pipeline = RAGPipeline(provider="openai")

@app.get("/")
async def root():
    return {
        "message": "Sepsis RAG API v2.0",
        "status": "operational",
        "endpoints": [
            "/analyze_patient",
            "/chat",
            "/health",
            "/stats"
        ]
    }

@app.get("/health")
async def health_check():
    try:
        stats = rag_pipeline.get_store_stats()
        return {
            "status": "healthy",
            "vector_store": "connected",
            "documents_loaded": stats.get("total_documents", 0)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@app.get("/stats")
async def get_statistics() -> Dict:
    try:
        return rag_pipeline.get_store_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")

@app.post("/analyze_patient", response_model=AnalysisResponse)
async def analyze_patient(request: AnalysisRequest):
    try:
        result = rag_pipeline.analyze_patient(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Analysis failed: {str(e)}"
        )

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = rag_pipeline.chat(request)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Chat failed: {str(e)}"
        )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

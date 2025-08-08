import os
import json
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from openai import AzureOpenAI
from typing import Dict, Any
import httpx
import json
from datetime import datetime

# ─── Local imports --- changed from . to /
from hybrid_retriever import search
from prompts import build_messages

# ─── Load config ───────────────────────────
load_dotenv()
ENDPOINT    = os.getenv("OPENAI_API_BASE")
API_KEY     = os.getenv("OPENAI_API_KEY")
API_VERSION = os.getenv("OPENAI_API_VERSION")
CHAT_MODEL  = os.getenv("CHAT_MODEL", "gpt-4.1")

# ─── AzureOpenAI client for chat ───────────
client = AzureOpenAI(
    azure_endpoint=ENDPOINT,
    api_key=API_KEY,
    api_version=API_VERSION,
)

app = FastAPI(
    title="BoundLy H1B API",
    description="AI-powered H-1B immigration analysis API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str

class QueryResponse(BaseModel):
    answer: str
    citations: list = []

@app.get("/")
async def root():
    return {
        "message": "BoundLy H1B API",
        "endpoints": {
            "POST /boundly/query": "Submit a question to get H1B-related answers"
        },
        "docs": "/docs"
    }

@app.post("/boundly/query")
async def query_boundly(request: QueryRequest) -> Dict[str, Any]:
    """
    Submit a question to get H-1B related analysis
    """
    try:
        # Get search results
        search_results = search(request.question)
        
        # Build messages for the AI
        messages = build_messages(request.question, search_results)
        
        # For now, return a mock response
        # In production, you would call your AI service here
        mock_answer = {
            "decision": "yes",
            "explanation": f"Based on your question: '{request.question}', here's a comprehensive analysis...",
            "citations": [result.get("source", "USCIS Guidelines") for result in search_results[:3]]
        }
        
        return {
            "answer": json.dumps(mock_answer),
            "citations": [result.get("source", "USCIS Guidelines") for result in search_results[:3]]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }

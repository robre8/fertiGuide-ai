from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager
import asyncio

app = FastAPI(title="FertiGuide AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Motor cargado lazy (no bloquea el arranque) ──
chat_engine = None

def get_chat_engine():
    global chat_engine
    if chat_engine is None:
        print("🔧 Building RAG pipeline on first request...")
        from rag.pipeline import build_chat_engine
        chat_engine = build_chat_engine()
    return chat_engine

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    engine = get_chat_engine()
    result = engine.chat(request.message)
    return ChatResponse(response=str(result))

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "pipeline_ready": chat_engine is not None
    }

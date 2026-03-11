from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import traceback

app = FastAPI(title="FertiGuide AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://ferti-guide-ai.vercel.app",
        os.getenv("FRONTEND_URL", "").rstrip("/")
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Return a proper JSON 500 so CORS headers are still attached."""
    traceback.print_exc()
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
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


@app.get("/")
async def root():
    return {"status": "FertiGuide AI Backend running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        engine = get_chat_engine()
        result = engine.chat(request.message)
        return ChatResponse(response=str(result))
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"response": f"Backend error: {e}"},
        )

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "pipeline_ready": chat_engine is not None
    }

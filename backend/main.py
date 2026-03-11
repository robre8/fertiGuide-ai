from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag.pipeline import build_chat_engine

app = FastAPI(title="FertiGuide AI Backend")

# Allow frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Build the AI pipeline once when server starts
print("🔧 Building RAG pipeline...")
chat_engine = build_chat_engine()


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    result = chat_engine.chat(request.message)
    return ChatResponse(response=str(result))


@app.get("/health")
async def health():
    return {"status": "ok"}

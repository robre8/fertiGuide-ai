from fastapi import FastAPI, Request, UploadFile, File, Header
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


ALLOWED_EXTENSIONS = {".pdf", ".txt"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@app.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    x_upload_secret: str = Header(None, alias="x-upload-secret"),
):
    """
    Upload a document to Supabase Storage and re-index all documents into Pinecone.
    Requires the X-Upload-Secret header to match the UPLOAD_SECRET env var.
    """
    expected_secret = os.getenv("UPLOAD_SECRET", "")
    if not expected_secret or x_upload_secret != expected_secret:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    filename = file.filename or ""
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content={"detail": f"Unsupported file type '{ext}'. Only PDF and TXT are allowed."},
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        return JSONResponse(
            status_code=413,
            content={"detail": "File too large. Maximum size is 20 MB."},
        )

    from rag.storage import upload_to_supabase
    upload_to_supabase(filename, content)
    print(f"📄 Uploaded '{filename}' to Supabase Storage")

    # Force re-index: clear Pinecone + re-ingest all docs from Supabase
    global chat_engine
    chat_engine = None
    from rag.pipeline import rebuild_index_from_supabase
    rebuild_index_from_supabase()

    return {"status": "ok", "filename": filename}


@app.get("/documents")
async def list_documents():
    """Return the list of documents currently stored in Supabase."""
    try:
        from rag.storage import list_supabase_documents
        docs = list_supabase_documents()
        return {"documents": docs}
    except Exception:
        return {"documents": []}

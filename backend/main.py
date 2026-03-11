from fastapi import FastAPI, Request, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import traceback
import threading

app = FastAPI(title="FertiGuide AI Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://ferti-guide-ai.vercel.app",
        os.getenv("FRONTEND_URL", "").rstrip("/")
    ],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*", "content-type", "x-upload-secret", "x-filename", "authorization"],
    expose_headers=["*"],
    max_age=600,
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
# Tracks whether a background reindex is in progress
_reindex_status = {"running": False, "last_error": None, "last_ok": None}

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
        "pipeline_ready": chat_engine is not None,
        "reindex_running": _reindex_status["running"],
    }


@app.get("/reindex-status")
async def reindex_status():
    return _reindex_status


ALLOWED_EXTENSIONS = {".pdf", ".txt"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@app.post("/upload")
async def upload_document(
    request: Request,
    x_upload_secret: str = Header(None, alias="x-upload-secret"),
    x_filename: str = Header(None, alias="x-filename"),
    secret: str = None,
    filename: str = None,
):
    """
    Upload a document to Supabase Storage and re-index all documents into Pinecone.
    Requires the X-Upload-Secret header to match the UPLOAD_SECRET env var.
    """
    # Accept secret from header OR query param
    provided_secret = x_upload_secret or request.query_params.get("secret", "")
    expected_secret = os.getenv("UPLOAD_SECRET", "")
    if not expected_secret or provided_secret != expected_secret:
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})

    content_type = (request.headers.get("content-type") or "").lower()
    filename = ""
    content = b""

    if "multipart/form-data" in content_type:
        try:
            form = await request.form()
        except Exception:
            return JSONResponse(
                status_code=400,
                content={"detail": "Could not parse multipart body. Please reselect the file and try again."},
            )
        uploaded = form.get("file")
        if uploaded is None:
            return JSONResponse(status_code=400, content={"detail": "Missing file field in form-data."})
        filename = getattr(uploaded, "filename", "") or ""
        content = await uploaded.read()
    else:
        filename = (x_filename or request.query_params.get("filename", "") or filename or "").strip()
        if not filename:
            return JSONResponse(
                status_code=400,
                content={"detail": "Missing filename. Send it in x-filename header."},
            )
        content = await request.body()

    if not content:
        return JSONResponse(status_code=400, content={"detail": "File is empty."})

    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content={"detail": f"Unsupported file type '{ext}'. Only PDF and TXT are allowed."},
        )

    if len(content) > MAX_FILE_SIZE:
        return JSONResponse(
            status_code=413,
            content={"detail": "File too large. Maximum size is 20 MB."},
        )

    from rag.storage import upload_to_supabase
    upload_to_supabase(filename, content)
    print(f"📄 Uploaded '{filename}' to Supabase Storage")

    # Reset engine and kick off reindex in the background so this
    # request can return immediately (avoids Render's 30-second timeout).
    global chat_engine
    chat_engine = None

    def _run_reindex():
        _reindex_status["running"] = True
        _reindex_status["last_error"] = None
        try:
            from rag.pipeline import rebuild_index_from_supabase, build_chat_engine
            rebuild_index_from_supabase()
            global chat_engine
            chat_engine = build_chat_engine()
            _reindex_status["last_ok"] = filename
            print(f"✅ Background reindex complete for '{filename}'")
        except Exception as exc:
            traceback.print_exc()
            _reindex_status["last_error"] = str(exc)
        finally:
            _reindex_status["running"] = False

    threading.Thread(target=_run_reindex, daemon=True).start()

    return {
        "status": "indexing",
        "filename": filename,
        "message": "File uploaded. Reindexing in background — chat will be ready in ~1 minute.",
    }


@app.get("/documents")
async def list_documents():
    """Return the list of documents currently stored in Supabase."""
    try:
        from rag.storage import list_supabase_documents
        docs = list_supabase_documents()
        return {"documents": docs}
    except Exception:
        return {"documents": []}

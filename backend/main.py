from fastapi import FastAPI, Request, Header
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import hashlib
import hmac
import os
import re
import time
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
    allow_credentials=True,
    max_age=600,
)

SESSION_COOKIE_NAME = "fertiguide_admin_session"
SESSION_TTL_SECONDS = int(os.getenv("SESSION_TTL_SECONDS", "28800"))
VERCEL_ORIGIN_RE = re.compile(r"^https://.*\.vercel\.app$")


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


def _allowed_origins() -> set[str]:
    origins = {
        "http://localhost:3000",
        "https://ferti-guide-ai.vercel.app",
    }
    frontend_url = os.getenv("FRONTEND_URL", "").rstrip("/")
    if frontend_url:
        origins.add(frontend_url)
    return origins


def _is_trusted_origin(origin: str | None) -> bool:
    if not origin:
        return False
    return origin in _allowed_origins() or bool(VERCEL_ORIGIN_RE.match(origin))


def _require_trusted_origin(request: Request) -> JSONResponse | None:
    origin = request.headers.get("origin")
    if origin and not _is_trusted_origin(origin):
        return JSONResponse(status_code=403, content={"detail": "Untrusted origin."})
    return None


def _admin_username() -> str:
    return os.getenv("ADMIN_USERNAME", "admin")


def _admin_password() -> str:
    return os.getenv("ADMIN_PASSWORD") or os.getenv("UPLOAD_SECRET", "")


def _session_secret() -> str:
    return os.getenv("SESSION_SECRET") or _admin_password()


def _sign_session(payload: str) -> str:
    secret = _session_secret().encode("utf-8")
    digest = hmac.new(secret, payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest


def _create_session_token(username: str) -> str:
    expires_at = int(time.time()) + SESSION_TTL_SECONDS
    payload = f"{username}:{expires_at}"
    signature = _sign_session(payload)
    return f"{payload}:{signature}"


def _verify_session_token(token: str | None) -> str | None:
    if not token:
        return None
    parts = token.split(":")
    if len(parts) != 3:
        return None
    username, expires_at_raw, signature = parts
    payload = f"{username}:{expires_at_raw}"
    expected_signature = _sign_session(payload)
    if not hmac.compare_digest(signature, expected_signature):
        return None
    try:
        expires_at = int(expires_at_raw)
    except ValueError:
        return None
    if expires_at < int(time.time()):
        return None
    return username


def _get_authenticated_admin(request: Request) -> str | None:
    return _verify_session_token(request.cookies.get(SESSION_COOKIE_NAME))


def _cookie_settings(request: Request) -> dict:
    forwarded_proto = request.headers.get("x-forwarded-proto", request.url.scheme)
    is_https = forwarded_proto == "https"
    return {
        "httponly": True,
        "secure": is_https,
        "samesite": "none" if is_https else "lax",
        "max_age": SESSION_TTL_SECONDS,
        "path": "/",
    }

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


class AdminLoginRequest(BaseModel):
    password: str
    username: str | None = None


@app.get("/")
async def root():
    return {"status": "FertiGuide AI Backend running"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if _reindex_status["running"]:
            return JSONResponse(
                status_code=503,
                content={"response": "Index is updating in background. Please try again in about a minute."},
            )

        engine = await run_in_threadpool(get_chat_engine)
        result = await run_in_threadpool(engine.chat, request.message)
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


@app.get("/admin/session")
async def admin_session(request: Request):
    username = _get_authenticated_admin(request)
    return {"authenticated": bool(username), "username": username}


@app.post("/admin/login")
async def admin_login(payload: AdminLoginRequest, request: Request):
    origin_error = _require_trusted_origin(request)
    if origin_error:
        return origin_error

    expected_password = _admin_password()
    if not expected_password:
        return JSONResponse(status_code=500, content={"detail": "Admin password is not configured."})

    provided_username = (payload.username or _admin_username()).strip()
    if provided_username != _admin_username() or payload.password != expected_password:
        return JSONResponse(status_code=401, content={"detail": "Invalid admin credentials."})

    response = JSONResponse(content={"authenticated": True, "username": provided_username})
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=_create_session_token(provided_username),
        **_cookie_settings(request),
    )
    return response


@app.post("/admin/logout")
async def admin_logout(request: Request):
    origin_error = _require_trusted_origin(request)
    if origin_error:
        return origin_error

    response = JSONResponse(content={"authenticated": False})
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/")
    return response


@app.get("/reindex-status")
async def reindex_status(request: Request):
    if not _get_authenticated_admin(request):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return _reindex_status


ALLOWED_EXTENSIONS = {".pdf", ".txt"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


@app.post("/upload")
async def upload_document(
    request: Request,
    x_filename: str = Header(None, alias="x-filename"),
    filename: str = None,
):
    """
    Upload a document to Supabase Storage and re-index all documents into Pinecone.
    Requires an authenticated admin session.
    """
    origin_error = _require_trusted_origin(request)
    if origin_error:
        return origin_error

    if not _get_authenticated_admin(request):
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
            from rag.pipeline import rebuild_index_from_supabase
            rebuild_index_from_supabase()
            # Let the next /chat request build a fresh engine in the request context.
            global chat_engine
            chat_engine = None
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
async def list_documents(request: Request):
    """Return the list of documents currently stored in Supabase."""
    if not _get_authenticated_admin(request):
        return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    try:
        from rag.storage import list_supabase_documents
        docs = list_supabase_documents()
        return {"documents": docs}
    except Exception:
        return {"documents": []}

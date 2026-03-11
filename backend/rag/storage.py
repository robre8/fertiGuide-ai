from supabase import create_client, Client
from pathlib import Path
import os
import tempfile

BUCKET = "documents"
DOCUMENTS_PATH = Path(__file__).parent.parent / "documents"


def get_supabase() -> Client:
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(url, key)


def upload_to_supabase(filename: str, content: bytes) -> str:
    """Upload a file to Supabase Storage and return its path."""
    sb = get_supabase()
    path = filename
    # Remove existing file if present (upsert)
    try:
        sb.storage.from_(BUCKET).remove([path])
    except Exception:
        pass
    sb.storage.from_(BUCKET).upload(path, content)
    return path


def download_all_from_supabase() -> list[Path]:
    """Download all documents from Supabase Storage to a temp dir and return paths."""
    sb = get_supabase()
    files = sb.storage.from_(BUCKET).list()
    if not files:
        return []

    tmp_dir = Path(tempfile.mkdtemp())
    downloaded = []
    for f in files:
        name = f["name"]
        if not name.endswith((".pdf", ".txt")):
            continue
        data = sb.storage.from_(BUCKET).download(name)
        dest = tmp_dir / name
        dest.write_bytes(data)
        downloaded.append(dest)
        print(f"  ↓ Downloaded {name} ({len(data)} bytes)")

    print(f"✅ Downloaded {len(downloaded)} files from Supabase")
    return downloaded


def list_supabase_documents() -> list[str]:
    """Return names of all files in the Supabase bucket."""
    sb = get_supabase()
    files = sb.storage.from_(BUCKET).list()
    return [f["name"] for f in files if f["name"].endswith((".pdf", ".txt"))]

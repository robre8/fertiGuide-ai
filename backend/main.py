from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from rag.pipeline import build_query_engine

app = FastAPI(title="fertiGuide Backend")

query_engine = None


class QueryRequest(BaseModel):
    question: str


@app.on_event("startup")
def startup_event() -> None:
    global query_engine
    documents_dir = Path(__file__).parent / "documents"
    try:
        query_engine = build_query_engine(str(documents_dir))
    except ValueError:
        # Allow API startup even when no key/PDFs are present yet.
        query_engine = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query")
def query_rag(payload: QueryRequest) -> dict[str, str]:
    if query_engine is None:
        raise HTTPException(
            status_code=503,
            detail="RAG pipeline is not ready. Check OPENAI_API_KEY and PDFs in backend/documents.",
        )

    result = query_engine.query(payload.question)
    return {"answer": str(result)}

# 🧬 FertiGuide AI

An intelligent clinical assistant for Assisted Reproductive Technology (ART), built with a production-grade RAG pipeline over real clinical documents.

**Live demo:** [ferti-guide-ai.vercel.app](https://ferti-guide-ai.vercel.app)

---

## What it does

- **Chat Q&A** — ask questions over uploaded clinical PDFs/TXTs using a RAG pipeline (LlamaIndex + Groq LLM).
- **Symptom Classifier** — lightweight client-side category classifier running entirely in the browser (no server roundtrip).
- **Document Upload** — password-protected panel to upload new PDFs/TXTs. Files are stored in Supabase Storage and automatically re-indexed into Pinecone.

---

## Architecture

```
Browser (Next.js / Vercel)
  ├── ChatBox         → POST /chat          → FastAPI (Render)
  ├── SymptomClassifier → ONNX inference in-browser (TensorFlow.js)
  └── DocumentUpload  → POST /upload        → FastAPI (Render)
                                                  ├── Supabase Storage  (PDF/TXT files)
                                                  └── Pinecone          (vector index)

Apollo GraphQL (optional layer, port 4000)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 · TypeScript · Tailwind CSS |
| Client AI | TensorFlow.js (ONNX, in-browser) |
| API layer | Apollo Server · GraphQL (TypeScript) |
| Backend | Python · FastAPI · Uvicorn |
| RAG framework | LlamaIndex (`CondensePlusContextChatEngine`) |
| LLM | Groq API — `llama-3.3-70b-versatile` |
| Embeddings | HuggingFace Inference API — `all-MiniLM-L6-v2` (384 dims) |
| Vector store | Pinecone (serverless, cosine, 384 dims) |
| Document store | Supabase Storage (private bucket `documents`) |
| Deploy | Vercel (frontend) · Render (backend) |

---

## Environment Variables

### Backend (Render)

| Variable | Description |
|---|---|
| `GROQ_API_KEY` | Groq API key |
| `HF_TOKEN` | HuggingFace token (for Inference API embeddings) |
| `PINECONE_API_KEY` | Pinecone API key |
| `PINECONE_INDEX_NAME` | Pinecone index name (default: `fertiguide`) |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (not anon key) |
| `UPLOAD_SECRET` | Password required to upload documents |

### Frontend (Vercel)

| Variable | Description |
|---|---|
| `NEXT_PUBLIC_BACKEND_URL` | Backend URL, e.g. `https://fertiguide-ai-backend.onrender.com` |
| `NEXT_PUBLIC_GRAPHQL_URL` | GraphQL API URL (optional) |

---

## Local Development

### 1. Backend
```bash
cd backend
cp .env.example .env   # fill in your keys
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 2. GraphQL API (optional)
```bash
cd api
npm install
npm run dev   # port 4000
```

### 3. Frontend
```bash
cd frontend
npm install
# create .env.local with NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
npm run dev   # port 3000
```

---

## Document Upload Flow

1. Open the **Upload Document** panel at the bottom of the app.
2. Enter the `UPLOAD_SECRET` password.
3. Select a PDF or TXT file (max 20 MB).
4. Click **Upload & Re-index**.
5. The file is stored in Supabase Storage.
6. Pinecone is cleared and re-indexed in the background (~1 minute).
7. Poll `GET /reindex-status` or wait ~1 minute before querying.

On backend restart, if Pinecone is empty it automatically downloads all files from Supabase and re-indexes them.

---

## Key Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | Health check |
| `GET` | `/health` | Pipeline + reindex status |
| `GET` | `/reindex-status` | Background reindex progress |
| `POST` | `/chat` | Send a message, get a RAG response |
| `POST` | `/upload` | Upload a document (requires `secret` query param) |
| `GET` | `/documents` | List documents in Supabase Storage |

---

## Pinecone Index Setup

Create a serverless index in Pinecone with:
- **Name:** `fertiguide` (or set `PINECONE_INDEX_NAME`)
- **Dimensions:** `384`
- **Metric:** `cosine`
- **Cloud/Region:** any free tier region

---

## Domain

Reproductive healthcare (ART) — IVF, IUI, FET protocols, hormonal guidance, and clinical document Q&A.

# 🧬 FertiGuide AI

An intelligent clinical assistant for Assisted Reproductive Technology (ART) 
clinics, built to demonstrate production-grade AI engineering across a modern 
full-stack architecture.

## What it does

FertiGuide AI allows patients and clinic staff to query fertility treatment 
protocols, understand lab results, and receive contextual guidance — all powered 
by a RAG (Retrieval-Augmented Generation) pipeline over real clinical documents.

A lightweight symptom classifier runs directly in the browser using TensorFlow.js, 
providing instant categorization without a server roundtrip.

## Tech Stack

- **Frontend:** Next.js + TypeScript + TensorFlow.js (ONNX client-side inference)
- **API Layer:** Apollo Server — GraphQL (TypeScript)
- **AI Backend:** Python + FastAPI + LlamaIndex + LangChain
- **Vector Store:** pgvector (PostgreSQL)
- **Embeddings:** Hugging Face SentenceTransformers
- **LLM:** Groq API / OpenAI compatible
- **Deploy:** Vercel (frontend) · Render (backend) · Supabase (DB)

## Domain

Reproductive healthcare (ART) — IVF, IUI, FET protocols, hormonal guidance, 
and fertility document Q&A.

## Status

🚧 Active development

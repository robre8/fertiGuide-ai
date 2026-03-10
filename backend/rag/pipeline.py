import os

from dotenv import load_dotenv
from llama_index.core import Settings, VectorStoreIndex
from llama_index.core.base.base_query_engine import BaseQueryEngine
from llama_index.llms.openai import OpenAI

from .loader import load_pdf_documents


def build_query_engine(documents_dir: str) -> BaseQueryEngine:
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is missing. Add it to backend/.env")

    documents = load_pdf_documents(documents_dir)
    if not documents:
        raise ValueError("No PDF files found in backend/documents")

    Settings.llm = OpenAI(model="gpt-4o-mini", api_key=api_key)

    index = VectorStoreIndex.from_documents(documents)
    return index.as_query_engine(similarity_top_k=3)

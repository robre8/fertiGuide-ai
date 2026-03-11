from llama_index.core import VectorStoreIndex, Settings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.llms.groq import Groq
from dotenv import load_dotenv
from rag.loader import load_documents
import os

load_dotenv()


def build_chat_engine():
    """
    Builds the full RAG pipeline with memory and returns a chat engine.
    """

    # 1. Embedding model (runs locally, no API key needed)
    embed_model = HuggingFaceEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

    # 2. LLM via Groq (fast and free) — native LlamaIndex integration
    llm = Groq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY")
    )

    # 3. Apply settings globally
    Settings.embed_model = embed_model
    Settings.llm = llm

    # 4. Load documents and build index in memory
    documents = load_documents()
    index = VectorStoreIndex.from_documents(documents)

    # 5. Add conversation memory
    memory = ChatMemoryBuffer.from_defaults(token_limit=3000)

    # 6. Build chat engine with context + memory
    chat_engine = CondensePlusContextChatEngine.from_defaults(
        retriever=index.as_retriever(similarity_top_k=3),
        memory=memory,
        verbose=True
    )

    print("✅ Chat engine ready")
    return chat_engine

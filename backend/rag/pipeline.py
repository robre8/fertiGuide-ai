import nest_asyncio
nest_asyncio.apply()

from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.huggingface_api import HuggingFaceInferenceAPIEmbedding
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.core.chat_engine import CondensePlusContextChatEngine
from llama_index.llms.groq import Groq
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import Pinecone
from dotenv import load_dotenv
from huggingface_hub import login
from rag.loader import load_documents
import os

load_dotenv()

hf_token = os.getenv("HF_TOKEN")
if hf_token:
    login(token=hf_token)

PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "fertiguide")


def build_chat_engine():
    """
    Builds the full RAG pipeline with Pinecone vector store and returns a chat engine.
    If the Pinecone index already has data, it skips re-indexing.
    """

    # 1. Embedding model via HF Inference API (no torch needed)
    embed_model = HuggingFaceInferenceAPIEmbedding(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        token=os.getenv("HF_TOKEN")
    )

    # 2. LLM via Groq (fast and free) — native LlamaIndex integration
    llm = Groq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY")
    )

    # 3. Apply settings globally
    Settings.embed_model = embed_model
    Settings.llm = llm

    # 4. Connect to Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    pinecone_index = pc.Index(PINECONE_INDEX_NAME)
    vector_store = PineconeVectorStore(pinecone_index=pinecone_index)

    # 5. Check if index already has vectors; if not, load and index documents
    stats = pinecone_index.describe_index_stats()
    total_vectors = stats.get("total_vector_count", 0)

    if total_vectors == 0:
        print("📥 Pinecone index is empty — indexing documents...")
        documents = load_documents()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context
        )
        print(f"✅ Indexed {len(documents)} chunks into Pinecone")
    else:
        print(f"✅ Pinecone index has {total_vectors} vectors — skipping re-index")
        index = VectorStoreIndex.from_vector_store(vector_store)

    # 6. Add conversation memory
    memory = ChatMemoryBuffer.from_defaults(token_limit=3000)

    # 7. Build chat engine with context + memory
    chat_engine = CondensePlusContextChatEngine.from_defaults(
        retriever=index.as_retriever(similarity_top_k=3),
        memory=memory,
        verbose=True
    )

    print("✅ Chat engine ready (Pinecone)")
    return chat_engine

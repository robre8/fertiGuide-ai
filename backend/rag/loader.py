from llama_index.core import SimpleDirectoryReader, Document
from pathlib import Path

DOCUMENTS_PATH = Path(__file__).parent.parent / "documents"


def load_documents() -> list[Document]:
    """
    Loads all PDF documents from the /documents folder.
    """
    if not any(DOCUMENTS_PATH.iterdir()):
        raise ValueError("No documents found in /documents folder. Add at least one PDF.")

    reader = SimpleDirectoryReader(
        input_dir=str(DOCUMENTS_PATH),
        required_exts=[".pdf", ".txt"]
    )

    documents = reader.load_data()
    print(f"✅ Loaded {len(documents)} document chunks")
    return documents

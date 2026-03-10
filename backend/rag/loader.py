from pathlib import Path

from llama_index.core import Document, SimpleDirectoryReader


def load_pdf_documents(documents_dir: str | Path) -> list[Document]:
    path = Path(documents_dir)
    path.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(path.glob("*.pdf"))
    if not pdf_files:
        return []

    reader = SimpleDirectoryReader(
        input_files=[str(file_path) for file_path in pdf_files],
        required_exts=[".pdf"],
    )
    return reader.load_data()

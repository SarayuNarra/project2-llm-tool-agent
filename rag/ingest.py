from pathlib import Path
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
VECTORSTORE_DIR = BASE_DIR / "vectorstore"
def load_documents():
    documents = []
    files = list(DATA_DIR.rglob("*"))
    supported_files = [
        file for file in files
        if file.suffix.lower() in [".pdf", ".docx"]
    ]
    if not supported_files:
        raise ValueError(
            f"No PDF or DOCX files found in: {DATA_DIR}"
        )
    for file in supported_files:
        print(f"Loading: {file}")
        extension = file.suffix.lower()
        if extension == ".pdf":
            loader = PyPDFLoader(
                str(file)
            )
        elif extension == ".docx":
            loader = Docx2txtLoader(
                str(file)
            )
        documents.extend(
            loader.load()
        )
    return documents
def create_vectorstore():
    documents = load_documents()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )
    chunks = splitter.split_documents(
        documents
    )
    print(
        f"Created {len(chunks)} chunks."
    )
    embeddings = HuggingFaceEmbeddings(
        model_name=
        "sentence-transformers/all-MiniLM-L6-v2"
    )
    vectorstore = FAISS.from_documents(
        chunks,
        embeddings
    )
    VECTORSTORE_DIR.mkdir(
        exist_ok=True
    )
    vectorstore.save_local(
        str(VECTORSTORE_DIR)
    )
    print(
        "Vector store created successfully."
    )
    print(
        f"Saved to: {VECTORSTORE_DIR}"
    )
if __name__ == "__main__":
    create_vectorstore()
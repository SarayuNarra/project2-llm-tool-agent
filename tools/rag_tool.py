from pathlib import Path
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

VECTORSTORE_DIR = Path(
    "vectorstore"
)
_embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
_vectorstore = None
def get_vectorstore():
    global _vectorstore
    if _vectorstore is None:
        if not VECTORSTORE_DIR.exists():
            raise FileNotFoundError(
                "Vector store not found. "
                "Run: python rag/ingest.py"
            )
        _vectorstore = FAISS.load_local(
            str(VECTORSTORE_DIR),
            _embeddings,
            allow_dangerous_deserialization=True
        )
    return _vectorstore
def rag_tool(query: str):
    vectorstore = get_vectorstore()
    documents = vectorstore.similarity_search(
        query,
        k=4
    )
    if not documents:
        return {
            "query": query,
            "context": "",
            "sources": []
        }
    context_parts = []
    sources = []
    for document in documents:
        context_parts.append(
            document.page_content
        )
        source = document.metadata.get(
            "source"
        )
        page = document.metadata.get(
            "page"
        )
        sources.append({
            "source": source,
            "page": page
        })
    return {
        "query": query,
        "context": "\n\n".join(
            context_parts
        ),
        "sources": sources
    }
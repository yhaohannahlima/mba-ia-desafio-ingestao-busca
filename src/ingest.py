import os
import time
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector

load_dotenv()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is not set")
    return value


def ingest_pdf():
    require_env("GOOGLE_API_KEY") # lida internamente pelo GoogleGenerativeAIEmbeddings
    pdf_path = require_env("PDF_PATH")
    collection_name = require_env("PG_VECTOR_COLLECTION_NAME")
    database_url = require_env("DATABASE_URL")

    docs = PyPDFLoader(pdf_path).load()
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    ).split_documents(docs)

    if not chunks:
        print("Nenhum conteúdo extraído do PDF.")
        return

    embeddings = GoogleGenerativeAIEmbeddings(
        model=os.getenv("GOOGLE_EMBEDDING_MODEL", "models/gemini-embedding-001")
    )

    batch_size = 10
    pause_seconds = 10

    store = PGVector(
        embeddings=embeddings,
        collection_name=collection_name,
        connection=database_url,
        use_jsonb=True,
        pre_delete_collection=True,
    )

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        store.add_documents(batch)
        print(f"{i + len(batch)}/{len(chunks)} chunks armazenados")
        if i + batch_size < len(chunks):
            time.sleep(pause_seconds)

    print(f"Ingestão concluída: {len(chunks)} chunks armazenados")


if __name__ == "__main__":
    ingest_pdf()

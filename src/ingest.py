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
    PDF_PATH = require_env("PDF_PATH")
    COLLECTION_NAME = require_env("PG_VECTOR_COLLECTION_NAME")
    DATABASE_URL = require_env("DATABASE_URL")

    docs = PyPDFLoader(PDF_PATH).load()
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

    BATCH_SIZE = 10
    PAUSE_SECONDS = 10

    store = PGVector(
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
        connection=DATABASE_URL,
        use_jsonb=True,
        pre_delete_collection=True,
    )

    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i:i + BATCH_SIZE]
        store.add_documents(batch)
        print(f"{i + len(batch)}/{len(chunks)} chunks armazenados")
        if i + BATCH_SIZE < len(chunks):
            time.sleep(PAUSE_SECONDS)

    print(f"Ingestão concluída: {len(chunks)} chunks armazenados")


if __name__ == "__main__":
    ingest_pdf()

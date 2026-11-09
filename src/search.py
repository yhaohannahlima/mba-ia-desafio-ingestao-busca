import os
from dotenv import load_dotenv

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_postgres import PGVector
from sqlalchemy import create_engine, inspect, text

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.

EXEMPLOS DE PERGUNTAS FORA DO CONTEXTO:
Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO"
"""

load_dotenv()


def count_chunks(database_url: str, collection_name: str) -> int:
    engine = create_engine(database_url)
    try:
        with engine.connect() as conn:
            if not inspect(conn).has_table("langchain_pg_collection"):
                return 0
            return conn.execute(
                text("""
                    SELECT COUNT(e.id)
                    FROM langchain_pg_collection c
                    LEFT JOIN langchain_pg_embedding e ON e.collection_id = c.uuid
                    WHERE c.name = :name
                """),
                {"name": collection_name},
            ).scalar_one()
    finally:
        engine.dispose()


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is not set")
    return value


def search_prompt():
    try:
        require_env("GOOGLE_API_KEY") # lida internamente pelos clientes Google GenAI
        collection_name = require_env("PG_VECTOR_COLLECTION_NAME")
        database_url = require_env("DATABASE_URL")

        if count_chunks(database_url, collection_name) == 0:
            raise RuntimeError(
                f"A collection '{collection_name}' não existe ou está vazia. "
                "Confira PG_VECTOR_COLLECTION_NAME ou rode src/ingest.py."
            )
        
        embeddings = GoogleGenerativeAIEmbeddings(
            model=os.getenv("GOOGLE_EMBEDDING_MODEL", "models/gemini-embedding-001")
        )

        store = PGVector(
            embeddings=embeddings,
            collection_name=collection_name,
            connection=database_url,
            use_jsonb=True,
        )

        llm = ChatGoogleGenerativeAI(
            model=os.getenv("GOOGLE_LLM_MODEL", "gemini-3.5-flash-lite"),
            max_retries=2,
        )
    except Exception as e:
        print(f"Erro ao inicializar a busca: {e}")
        return None

    def search_context(pergunta: str) -> str:
        results = store.similarity_search_with_score(pergunta, k=10)
        return "\n\n---\n\n".join(doc.page_content for doc, _score in results)

    prompt = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)

    return (
        {"contexto": RunnableLambda(search_context), "pergunta": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
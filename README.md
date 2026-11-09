# Desafio MBA Engenharia de Software com IA - Full Cycle

Ingestão e busca semântica com LangChain: um PDF é dividido em chunks, vetorizado com Gemini e armazenado no PostgreSQL com pgVector. Um chat no terminal responde perguntas **somente** com base no conteúdo do PDF.

## Stack

- **Python 3.13** + **LangChain**
- **Google Gemini**
  - Embeddings: `models/gemini-embedding-001`
  - LLM: `gemini-3.5-flash-lite`
- **PostgreSQL 17 + pgVector** (via Docker Compose)

## Estrutura

```text
├── docker-compose.yml   # PostgreSQL + extensão pgVector
├── document.pdf         # PDF a ser ingerido
├── requirements.txt
├── .env.example         # Modelo das variáveis de ambiente
└── src/
    ├── ingest.py        # Ingestão: PDF → chunks → embeddings → pgVector
    ├── search.py        # Busca semântica + chain com o LLM
    └── chat.py          # CLI interativa
```

## Pré-requisitos

- Python 3.13
- Docker e Docker Compose
- Uma chave de API do Google Gemini ([Google AI Studio](https://aistudio.google.com/apikey))

## Como executar

### 1. Criar o ambiente virtual e instalar as dependências

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configurar as variáveis de ambiente

```bash
cp .env.example .env
```

Preencha o `.env`:

| Variável                    | Valor                                               | Obrigatória           |
| --------------------------- | --------------------------------------------------- | --------------------- |
| `GOOGLE_API_KEY`            | Sua chave da API do Gemini                          | Sim                   |
| `DATABASE_URL`              | `postgresql://postgres:postgres@localhost:5432/rag` | Sim                   |
| `PG_VECTOR_COLLECTION_NAME` | Nome da collection, por exemplo `documents`         | Sim                   |
| `PDF_PATH`                  | `document.pdf`                                      | Sim                   |
| `GOOGLE_EMBEDDING_MODEL`    | `models/gemini-embedding-001`                       | Não (este é o padrão) |
| `GOOGLE_LLM_MODEL`          | `gemini-3.5-flash-lite`                             | Não (este é o padrão) |

> As variáveis `OPENAI_*` não são usadas nesta solução.
>
> **Atenção:** se `GOOGLE_EMBEDDING_MODEL` ou `GOOGLE_LLM_MODEL` estiverem no `.env` com valor vazio, o padrão não é aplicado. Preencha a variável ou remova a linha.

### 3. Subir o banco de dados

```bash
docker compose up -d
```

Esse comando sobe o PostgreSQL na porta `5432` e cria a extensão `vector` automaticamente.

### 4. Executar a ingestão do PDF

```bash
python src/ingest.py
```

O PDF é dividido em chunks de 1000 caracteres com 150 de sobreposição. Os chunks são enviados em lotes, com pausa entre eles, para respeitar o limite de tokens por minuto do plano gratuito do Gemini. Saída esperada:

```text
10/67 chunks armazenados
...
67/67 chunks armazenados
Ingestão concluída: 67 chunks armazenados
```

A ingestão pode ser executada novamente: a collection é recriada a cada execução, então os chunks não são duplicados.

### 5. Iniciar o chat

```bash
python src/chat.py
```

Para sair, digite `sair` ou pressione `Ctrl+C`.

## Exemplo de uso

```text
PERGUNTA: Qual o faturamento da Empresa SuperTechIABrazil?
RESPOSTA: R$ 10.000.000,00.

PERGUNTA: Quantos clientes temos em 2024?
RESPOSTA: Não tenho informações necessárias para responder sua pergunta.
```

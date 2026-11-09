from google.api_core.exceptions import ResourceExhausted
from sqlalchemy.exc import OperationalError

from search import search_prompt

EXIT_COMMANDS = {"sair", "exit", "quit"}


def friendly_error(e: Exception) -> str:
    current = e
    while current:
        if isinstance(current, ResourceExhausted):
            return "Limite de uso da API do Gemini atingido. Aguarde cerca de 1 minuto e tente novamente."
        if isinstance(current, OperationalError):
            return "Não foi possível acessar o banco de dados. Verifique se o container está rodando (docker compose up -d)."
        current = current.__cause__
    return f"Erro inesperado ao processar a pergunta: {e}"


def main():
    chain = search_prompt()

    if not chain:
        print("Não foi possível iniciar o chat. Verifique os erros de inicialização.")
        return
    
    print("Chat iniciado. Digite 'sair' para encerrar.\n")

    try:
        while True:
            question = input("PERGUNTA: ").strip()

            if not question:
                continue
            if question.lower() in EXIT_COMMANDS:
                break

            try:
                answer = chain.invoke(question)
            except Exception as e:
                print(f"{friendly_error(e)}\n")
                continue

            print(f"RESPOSTA: {answer}\n")
    except (KeyboardInterrupt, EOFError):
        print()

    print("Encerrando o chat.")


if __name__ == "__main__":
    main()
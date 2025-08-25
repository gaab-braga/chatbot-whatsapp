import openai
import os
from.rag_utils import buscar_contexto_relevante

# A API Key é configurada automaticamente pela variável de ambiente OPENAI_API_KEY
# openai.api_key = os.getenv("OPENAI_API_KEY")

def gerar_resposta(mensagem, historico):
    """
    Gera uma resposta inteligente usando a API da OpenAI, enriquecida com
    contexto de uma base de conhecimento (RAG).
    """
    try:
        # 1. Buscar contexto relevante na base de conhecimento
        contexto_rag = buscar_contexto_relevante(mensagem)
        
        # 2. Construir o histórico formatado para o prompt
        historico_formatado = "\n".join([f"Usuário: {h['user']} | Bot: {h['bot']}" for h in historico])
        
        # 3. Criar um prompt de sistema robusto
        system_prompt = f"""
        Você é um assistente virtual. Sua personalidade é prestativa e eficiente.
        Responda as perguntas do usuário com base no histórico da conversa e no CONTEXTO ADICIONAL fornecido.
        Se o CONTEXTO ADICIONAL tiver a resposta, priorize essa informação.
        Se você não souber a resposta ou a pergunta for sobre um tópico sensível, responda com a palavra-chave "handoff".

        CONTEXTO ADICIONAL:
        ---
        {contexto_rag}
        ---
        """

        # 4. Montar a lista de mensagens para a API
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Histórico da conversa:\n{historico_formatado}\n\nPergunta atual: {mensagem}"}
        ]

        # 5. Chamar a API da OpenAI
        client = openai.OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.7
        )

        return response.choices.message.content.strip()

    # Tratamento de erros específicos da API
    except openai.RateLimitError:
        print("Erro: Rate limit da OpenAI atingido.")
        return "Estou recebendo muitas perguntas no momento. Por favor, aguarde um instante."
    except Exception as e:
        print(f"Erro inesperado na API da OpenAI: {e}")
        return "Desculpe, não consegui processar sua solicitação. Digite 'atendente' para falar com um humano."
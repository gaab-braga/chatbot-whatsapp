# utils.py
import os
from openai import OpenAI

# Cliente OpenAI autenticado
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Histórico em memória: {sender_id: [mensagens ...]}
conversation_history = {}

def generate_ai_response(sender_id, user_message):
    """
    Gera resposta de IA via OpenAI, mantendo contexto do diálogo.
    """
    # Inicializa histórico se novo usuário
    if sender_id not in conversation_history:
        conversation_history[sender_id] = []
    # Adiciona mensagem do usuário ao histórico
    conversation_history[sender_id].append({"role": "user", "content": user_message})

    # Define prompt do sistema (tom e regras do bot)
    system_prompt = {
        "role": "system",
        "content": (
            "Você é um assistente virtual amigável e eficiente de uma startup inovadora. "
            "Suas respostas devem ser claras, concisas e úteis. Não invente informações."
        )
    }
    # Concatena prompt do sistema + histórico
    messages = [system_prompt] + conversation_history[sender_id]

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        # Extrai texto gerado
        ai_message = response.choices[0].message.content
        # Adiciona resposta da IA ao histórico
        conversation_history[sender_id].append({"role": "assistant", "content": ai_message})

        # Limita tamanho do histórico para não ficar muito longo
        if len(conversation_history[sender_id]) > 10:
            conversation_history[sender_id] = conversation_history[sender_id][-10:]
        return ai_message

    except Exception as e:
        print(f"Erro ao chamar API de IA: {e}")
        return "Desculpe, estou com um problema técnico no momento. Tente novamente mais tarde."

def handle_human_handoff(sender_id, user_message):
    """
    Lógica para iniciar transbordo humano.
    Simula notificação (por exemplo, poderia integrar Slack/email aqui).
    """
    print(f"*** HANDOFF TRIGGERED for {sender_id} ***")
    print(f"Última mensagem: '{user_message}'")
    print("Histórico da conversa:", conversation_history.get(sender_id, []))

    # Em produção: enviar notificação real (Slack webhook, e-mail, ticket etc.)
    # Aqui apenas retornamos mensagem de confirmação ao usuário.
    return (
        "Entendido. Um de nossos especialistas entrará em contato em breve "
        "via este chat. Obrigado por aguardar."
    )

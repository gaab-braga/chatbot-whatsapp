import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

try:
    client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
    channel_id = os.getenv("SLACK_CHANNEL_ID")
except Exception as e:
    print(f"Erro ao inicializar cliente Slack: {e}")
    client = None
    channel_id = None

def enviar_slack(mensagem):
    """Função base para enviar uma mensagem para um canal no Slack."""
    if not client or not channel_id:
        print("Credenciais do Slack não configuradas. Mensagem não enviada.")
        return

    try:
        client.chat_postMessage(channel=channel_id, text=mensagem)
    except SlackApiError as e:
        print(f"Erro ao enviar mensagem para o Slack: {e.response['error']}")

def notificar_inicio_handoff(user_number, initial_message):
    """Notifica a equipe que um novo atendimento humano foi solicitado."""
    mensagem = f"👤 *Handoff Iniciado*\n*Usuário:* {user_number}\n*Solicitação:* '{initial_message}'"
    enviar_slack(mensagem)

def encaminhar_mensagem_para_suporte(user_number, message):
    """Encaminha mensagens de um usuário que já está em atendimento humano."""
    mensagem = f"📩 *Nova Mensagem (Handoff)*\n*De:* {user_number}\n*Mensagem:* {message}"
    enviar_slack(mensagem)
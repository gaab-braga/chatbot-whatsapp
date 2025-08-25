from flask import Blueprint, request, Response
from functools import wraps
import os
from twilio.twiml.messaging_response import MessagingResponse
from twilio.request_validator import RequestValidator
from utils.openai_utils import gerar_resposta
from utils.redis_utils import obter_sessao, salvar_sessao, adicionar_mensagem_ao_historico
from utils.slack_utils import notificar_inicio_handoff, encaminhar_mensagem_para_suporte
from utils.email_utils import enviar_email

whatsapp_bp = Blueprint("whatsapp", __name__)

def validate_twilio_request(f):
    """Valida que a requisição veio da Twilio, protegendo o webhook."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        validator = RequestValidator(os.environ.get('TWILIO_AUTH_TOKEN'))
        
        request_url = request.url
        post_vars = request.form.to_dict()
        twilio_signature = request.headers.get('X-Twilio-Signature', '')

        if not validator.validate(request_url, post_vars, twilio_signature):
            return "Requisição inválida.", 403
        return f(*args, **kwargs)
    return decorated_function

@whatsapp_bp.route("/message", methods=)
@validate_twilio_request
def message():
    """Recebe, processa e responde às mensagens do WhatsApp com lógica de handoff."""
    data = request.form
    user_number = data.get("From")
    user_message = data.get("Body")

    # Obtém a sessão completa do usuário, incluindo o estado de handoff
    sessao = obter_sessao(user_number)

    # --- LÓGICA DE HANDOFF ---
    HANDOFF_TRIGGERS = ["humano", "atendente", "suporte", "falar com alguém", "ajuda humana"]

    # 1. Se o usuário JÁ ESTÁ em modo handoff, apenas encaminha a mensagem
    if sessao.get("handoff_ativo", False):
        encaminhar_mensagem_para_suporte(user_number, user_message)
        # Retorna uma resposta TwiML vazia para que o bot não responda ao usuário
        return Response(str(MessagingResponse()), mimetype="application/xml")

    # 2. Se o usuário ACIONOU o handoff nesta mensagem
    if any(trigger in user_message.lower() for trigger in HANDOFF_TRIGGERS):
        sessao["handoff_ativo"] = True
        salvar_sessao(user_number, sessao)
        
        # Notifica a equipe sobre o início do atendimento humano
        notificar_inicio_handoff(user_number, user_message)
        
        resposta_final = "Certo! Um de nossos especialistas assumirá a conversa em breve. Qualquer outra mensagem que você enviar agora será lida por eles."
        
        twiml_response = MessagingResponse()
        twiml_response.message(resposta_final)
        return Response(str(twiml_response), mimetype="application/xml")

    # --- LÓGICA NORMAL DO BOT (se não houver handoff) ---
    
    # Gera resposta usando a IA com o histórico da sessão
    resposta_ia = gerar_resposta(user_message, sessao.get("historico", ))

    # Verifica se a própria IA sugeriu o handoff
    if resposta_ia.lower() == "handoff":
        sessao["handoff_ativo"] = True
        resposta_final = "Entendi. Um de nossos especialistas entrará em contato com você em breve."
        notificar_inicio_handoff(user_number, f"IA sugeriu handoff para a mensagem: '{user_message}'")
    else:
        resposta_final = resposta_ia

    # Adiciona a interação ao histórico da sessão e salva tudo no Redis
    sessao = adicionar_mensagem_ao_historico(sessao, user_message, resposta_final)
    salvar_sessao(user_number, sessao)

    # Envia a resposta final ao usuário
    twiml_response = MessagingResponse()
    twiml_response.message(resposta_final)
    return Response(str(twiml_response), mimetype="application/xml")
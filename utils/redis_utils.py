import os
import json
import redis

# Conecta ao Redis usando a URL fornecida nas variáveis de ambiente
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
r = redis.from_url(redis_url, decode_responses=True)

def obter_sessao(user_id):
    """
    Obtém a sessão completa do usuário do Redis.
    Retorna um objeto de sessão padrão se não existir.
    """
    try:
        dados = r.get(user_id)
        if dados:
            return json.loads(dados)
    except Exception as e:
        print(f"Erro ao obter sessão no Redis para {user_id}: {e}")
    
    # Retorna uma sessão padrão se não houver dados
    return {"historico": [], "handoff_ativo": False}

def salvar_sessao(user_id, session_data):
    """Salva o objeto de sessão completo no Redis."""
    try:
        # Define um tempo de expiração para a chave (ex: 24 horas)
        r.set(user_id, json.dumps(session_data), ex=86400)
    except Exception as e:
        print(f"Erro ao salvar sessão no Redis para {user_id}: {e}")

def adicionar_mensagem_ao_historico(session_data, user_msg, bot_msg, max_historico=10):
    """Adiciona uma nova interação ao histórico dentro do objeto de sessão."""
    if "historico" not in session_data:
        session_data["historico"] = []
    
    session_data["historico"].append({"user": user_msg, "bot": bot_msg})
    
    # Mantém o histórico com um tamanho gerenciável
    session_data["historico"] = session_data["historico"][-max_historico:]
    
    return session_data
"""Redis (sessão), e-mail e Slack com clientes falsos."""
from types import SimpleNamespace

from utils import email_utils, redis_utils, slack_utils


def test_sessao_nova_tem_padrao(redis_falso):
    assert redis_utils.obter_sessao("ninguem") == {"historico": [], "handoff_ativo": False}


def test_sessao_salva_e_lida(redis_falso):
    sessao = {"historico": [{"user": "a", "bot": "b"}], "handoff_ativo": True}
    redis_utils.salvar_sessao("u1", sessao)
    assert redis_utils.obter_sessao("u1") == sessao


def test_redis_fora_do_ar_devolve_sessao_padrao(monkeypatch):
    class RedisQuebrado:
        def get(self, chave):
            raise ConnectionError("sem redis")

    monkeypatch.setattr(redis_utils, "r", RedisQuebrado())
    assert redis_utils.obter_sessao("u1") == {"historico": [], "handoff_ativo": False}


def test_historico_e_criado_e_cortado():
    sessao = {}
    for i in range(12):
        sessao = redis_utils.adicionar_mensagem_ao_historico(sessao, f"p{i}", f"r{i}")
    assert len(sessao["historico"]) == 10
    assert sessao["historico"][0] == {"user": "p2", "bot": "r2"}


def test_email_monta_cabecalhos_e_envia(monkeypatch):
    enviados = []

    class SMTPFalso:
        def __init__(self, servidor, porta):
            enviados.append(("conexao", servidor, porta))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def starttls(self):
            enviados.append(("tls",))

        def login(self, usuario, senha):
            enviados.append(("login", usuario))

        def send_message(self, msg):
            enviados.append(("msg", msg))

    for chave, valor in {
        "EMAIL_USER": "bot@exemplo.test",
        "EMAIL_PASS": "senha-falsa",
        "EMAIL_TO": "suporte@exemplo.test",
        "SMTP_SERVER": "smtp.exemplo.test",
        "SMTP_PORT": "587",
    }.items():
        monkeypatch.setenv(chave, valor)
    monkeypatch.setattr(email_utils.smtplib, "SMTP", SMTPFalso)

    email_utils.enviar_email("Novo handoff", "Corpo do e-mail")

    assert enviados[0] == ("conexao", "smtp.exemplo.test", 587)
    msg = enviados[-1][1]
    assert msg["Subject"] == "Novo handoff"
    assert msg["From"] == "bot@exemplo.test"
    assert msg["To"] == "suporte@exemplo.test"
    assert msg.get_payload() == "Corpo do e-mail"


def test_slack_notifica_handoff(monkeypatch):
    postados = []
    monkeypatch.setattr(
        slack_utils, "client", SimpleNamespace(chat_postMessage=lambda **kw: postados.append(kw))
    )
    monkeypatch.setattr(slack_utils, "channel_id", "C-FALSO")

    slack_utils.notificar_inicio_handoff("whatsapp:+5500000000000", "quero um atendente")

    assert postados[0]["channel"] == "C-FALSO"
    assert "whatsapp:+5500000000000" in postados[0]["text"]


def test_slack_sem_credenciais_nao_quebra(monkeypatch):
    monkeypatch.setattr(slack_utils, "channel_id", None)
    slack_utils.enviar_slack("teste")

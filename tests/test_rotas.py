"""Webhook /whatsapp/message com Twilio (validação), Redis, IA e Slack falsos."""
import json
import xml.etree.ElementTree as ET

import pytest

from app import create_app
from routes import whatsapp_routes as rotas

NUMERO = "whatsapp:+5500000000000"  # número fictício


@pytest.fixture
def ambiente(monkeypatch, redis_falso):
    estado = {"assinatura_valida": True, "resposta_ia": "Resposta da IA.", "ia": [], "slack": []}

    class ValidadorFalso:
        def __init__(self, token):
            pass

        def validate(self, url, parametros, assinatura):
            return estado["assinatura_valida"]

    def gerar_resposta_falsa(mensagem, historico):
        estado["ia"].append((mensagem, list(historico)))
        return estado["resposta_ia"]

    monkeypatch.setattr(rotas, "RequestValidator", ValidadorFalso)
    monkeypatch.setattr(rotas, "gerar_resposta", gerar_resposta_falsa)
    monkeypatch.setattr(rotas, "notificar_inicio_handoff", lambda n, m: estado["slack"].append(("inicio", n, m)))
    monkeypatch.setattr(rotas, "encaminhar_mensagem_para_suporte", lambda n, m: estado["slack"].append(("msg", n, m)))
    estado["redis"] = redis_falso
    estado["cliente"] = create_app().test_client()
    return estado


def enviar(ambiente, corpo):
    dados = {"From": NUMERO}
    if corpo is not None:
        dados["Body"] = corpo
    return ambiente["cliente"].post(
        "/whatsapp/message", data=dados, headers={"X-Twilio-Signature": "assinatura-falsa"}
    )


def mensagens_twiml(resposta):
    assert resposta.status_code == 200
    assert resposta.mimetype == "application/xml"
    raiz = ET.fromstring(resposta.data)
    assert raiz.tag == "Response"
    return [m.text for m in raiz.findall("Message")]


def test_mensagem_normal_responde_twiml_com_a_ia(ambiente):
    resposta = enviar(ambiente, "Qual o prazo de entrega?")

    assert mensagens_twiml(resposta) == ["Resposta da IA."]
    assert ambiente["ia"] == [("Qual o prazo de entrega?", [])]
    sessao = ambiente["redis"].sessao(NUMERO)
    assert sessao["handoff_ativo"] is False
    assert sessao["historico"] == [{"user": "Qual o prazo de entrega?", "bot": "Resposta da IA."}]


def test_segunda_mensagem_leva_o_historico(ambiente):
    enviar(ambiente, "Oi")
    enviar(ambiente, "E o frete?")

    assert ambiente["ia"][1] == ("E o frete?", [{"user": "Oi", "bot": "Resposta da IA."}])


def test_gatilho_de_atendente_inicia_handoff(ambiente):
    resposta = enviar(ambiente, "Quero falar com um ATENDENTE")

    (texto,) = mensagens_twiml(resposta)
    assert "especialistas" in texto
    assert ambiente["ia"] == []
    assert ambiente["slack"] == [("inicio", NUMERO, "Quero falar com um ATENDENTE")]
    assert ambiente["redis"].sessao(NUMERO)["handoff_ativo"] is True


def test_em_handoff_encaminha_e_nao_responde(ambiente):
    ambiente["redis"].set(NUMERO, json.dumps({"historico": [], "handoff_ativo": True}))

    resposta = enviar(ambiente, "Alguém aí?")

    assert mensagens_twiml(resposta) == []
    assert ambiente["slack"] == [("msg", NUMERO, "Alguém aí?")]
    assert ambiente["ia"] == []


def test_ia_pede_handoff(ambiente):
    ambiente["resposta_ia"] = "handoff"

    resposta = enviar(ambiente, "Tenho um problema jurídico")

    (texto,) = mensagens_twiml(resposta)
    assert "especialistas" in texto
    assert ambiente["slack"][0][0] == "inicio"
    assert ambiente["redis"].sessao(NUMERO)["handoff_ativo"] is True


def test_assinatura_invalida_da_403(ambiente):
    ambiente["assinatura_valida"] = False

    resposta = enviar(ambiente, "Oi")

    assert resposta.status_code == 403
    assert ambiente["ia"] == []


def test_get_nao_e_aceito(ambiente):
    assert ambiente["cliente"].get("/whatsapp/message").status_code == 405


def test_mensagem_sem_texto_nao_quebra(ambiente):
    # Ex.: o usuário manda só uma foto; o campo Body pode não vir.
    resposta = enviar(ambiente, None)
    assert resposta.status_code == 200

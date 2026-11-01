"""gerar_resposta com um cliente OpenAI falso: nenhuma chave, nenhuma chamada de rede."""
from types import SimpleNamespace

import pytest

from utils import openai_utils


@pytest.fixture
def openai_falso(monkeypatch):
    chamadas = []

    class OpenAIFalso:
        def __init__(self, *args, **kwargs):
            self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

        def _create(self, **kwargs):
            chamadas.append(kwargs)
            mensagem = SimpleNamespace(content="  Resposta falsa.  ")
            return SimpleNamespace(choices=[SimpleNamespace(message=mensagem)])

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(openai_utils.openai, "OpenAI", OpenAIFalso)
    monkeypatch.setattr(
        openai_utils, "buscar_contexto_relevante", lambda pergunta: f"CONTEXTO-FALSO para: {pergunta}"
    )
    return chamadas


def test_gerar_resposta_monta_prompt_com_contexto(openai_falso):
    historico = [{"user": "Oi", "bot": "Olá!"}]

    resposta = openai_utils.gerar_resposta("Qual o prazo de entrega?", historico)

    assert resposta == "Resposta falsa."
    assert len(openai_falso) == 1
    chamada = openai_falso[0]
    assert chamada["model"] == "gpt-4o-mini"
    sistema, usuario = chamada["messages"]
    assert sistema["role"] == "system"
    assert "CONTEXTO-FALSO para: Qual o prazo de entrega?" in sistema["content"]
    assert usuario["role"] == "user"
    assert "Usuário: Oi | Bot: Olá!" in usuario["content"]
    assert "Pergunta atual: Qual o prazo de entrega?" in usuario["content"]


def test_gerar_resposta_sem_historico(openai_falso):
    assert openai_utils.gerar_resposta("Oi", []) == "Resposta falsa."


def test_erro_da_api_devolve_mensagem_amigavel(monkeypatch):
    class OpenAIQueFalha:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("sem rede")

    monkeypatch.setattr(openai_utils.openai, "OpenAI", OpenAIQueFalha)
    monkeypatch.setattr(openai_utils, "buscar_contexto_relevante", lambda pergunta: "")

    assert "atendente" in openai_utils.gerar_resposta("Oi", [])

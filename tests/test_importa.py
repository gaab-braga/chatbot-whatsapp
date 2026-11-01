"""O projeto precisa, antes de tudo, importar e subir."""
import importlib

import pytest

MODULOS = [
    "app",
    "routes.whatsapp_routes",
    "utils.openai_utils",
    "utils.rag_utils",
    "utils.redis_utils",
    "utils.slack_utils",
    "utils.email_utils",
]


@pytest.mark.parametrize("nome", MODULOS)
def test_modulo_importa(nome):
    importlib.import_module(nome)


def test_app_responde_na_raiz():
    from app import create_app

    resposta = create_app().test_client().get("/")
    assert resposta.status_code == 200


def test_cliente_openai_e_criado_sem_rede():
    # Só cria o cliente (não chama a API). Falha se a versão do openai
    # for incompatível com a do httpx instalada.
    import openai

    openai.OpenAI(api_key="chave-falsa-de-teste")

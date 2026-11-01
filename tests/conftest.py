import json

import pytest


class RedisFalso:
    """Substitui o cliente Redis: guarda as chaves num dicionário."""

    def __init__(self):
        self.dados = {}

    def get(self, chave):
        return self.dados.get(chave)

    def set(self, chave, valor, ex=None):
        self.dados[chave] = valor

    def sessao(self, chave):
        return json.loads(self.dados[chave])


@pytest.fixture
def redis_falso(monkeypatch):
    from utils import redis_utils

    falso = RedisFalso()
    monkeypatch.setattr(redis_utils, "r", falso)
    return falso

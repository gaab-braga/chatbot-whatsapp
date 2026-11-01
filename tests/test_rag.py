"""Busca semântica: embeddings (all-MiniLM-L6-v2) + índice FAISS."""
import faiss
import pytest

from utils import rag_utils

CHUNKS_PEQUENOS = [
    "O prazo de troca é de 30 dias após o recebimento.",
    "Entregamos em todo o Brasil pelos Correios.",
    "Aceitamos Pix, boleto e cartão de crédito.",
    "A loja física abre de segunda a sábado, das 9h às 18h.",
]


@pytest.fixture
def base_pequena(monkeypatch):
    monkeypatch.setattr(rag_utils, "chunks_globais", CHUNKS_PEQUENOS)
    monkeypatch.setattr(
        rag_utils, "indice_faiss_global", rag_utils.criar_indice_faiss(CHUNKS_PEQUENOS)
    )


def test_base_de_conhecimento_carregada():
    assert rag_utils.chunks_globais, "base vazia ou caminho errado"
    assert 15 <= len(rag_utils.chunks_globais) <= 30


def test_base_carrega_de_qualquer_pasta(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert rag_utils.carregar_documentos(rag_utils.KNOWLEDGE_BASE_PATH)


def test_base_e_marcada_como_ficticia():
    with open(rag_utils.KNOWLEDGE_BASE_PATH, encoding="utf-8") as f:
        assert "fictícia" in f.read().lower()


def test_indice_faiss_criado():
    indice = rag_utils.criar_indice_faiss(["primeiro texto", "segundo texto", "terceiro texto"])
    assert isinstance(indice, faiss.Index)
    assert indice.ntotal == 3
    assert indice.d == 384  # dimensão do all-MiniLM-L6-v2


def test_indice_de_lista_vazia_e_none():
    assert rag_utils.criar_indice_faiss([]) is None


def test_busca_devolve_textos_da_base(base_pequena):
    contexto = rag_utils.buscar_contexto_relevante("Qual o prazo para trocar um produto?", top_k=2)
    partes = contexto.split("\n---\n")
    assert len(partes) == 2
    assert all(p in CHUNKS_PEQUENOS for p in partes)
    assert partes[0] == CHUNKS_PEQUENOS[0]


def test_top_k_maior_que_a_base_nao_repete_texto(base_pequena):
    # O FAISS completa com -1 quando faltam vizinhos; -1 não pode virar "o último chunk".
    contexto = rag_utils.buscar_contexto_relevante("pagamento", top_k=10)
    partes = contexto.split("\n---\n")
    assert sorted(partes) == sorted(CHUNKS_PEQUENOS)


def test_busca_na_base_real_devolve_tres_paragrafos():
    contexto = rag_utils.buscar_contexto_relevante("Como funciona a troca?")
    partes = contexto.split("\n---\n")
    assert len(partes) == 3
    assert all(p in rag_utils.chunks_globais for p in partes)


def test_busca_sem_indice_devolve_vazio(monkeypatch):
    monkeypatch.setattr(rag_utils, "indice_faiss_global", None)
    assert rag_utils.buscar_contexto_relevante("qualquer coisa") == ""

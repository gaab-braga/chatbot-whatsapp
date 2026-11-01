"""O conjunto de perguntas da avaliação precisa ser válido e o script precisa rodar."""
import json
from pathlib import Path

from utils import rag_utils

PERGUNTAS = Path(__file__).resolve().parents[1] / "avaliacao" / "perguntas.json"


def carregar_perguntas():
    return json.loads(PERGUNTAS.read_text(encoding="utf-8"))


def test_conjunto_tem_de_15_a_30_perguntas():
    assert 15 <= len(carregar_perguntas()) <= 30


def test_cada_esperado_aponta_para_um_unico_paragrafo():
    for item in carregar_perguntas():
        achados = [c for c in rag_utils.chunks_globais if c.startswith(item["esperado"] + ":")]
        assert len(achados) == 1, item


def test_script_de_avaliacao_devolve_hit_rate():
    from avaliacao.avaliar_busca import avaliar

    resultado = avaliar(top_k=3)
    assert resultado["n"] == len(carregar_perguntas())
    assert 0.0 <= resultado["hit_rate"] <= 1.0
    assert 0.0 <= resultado["hit_rate_top1"] <= resultado["hit_rate"]

"""Avaliação da busca (RAG): a pergunta traz o parágrafo certo entre os top_k?

Mede só a busca (embeddings + FAISS). Não mede a qualidade da resposta do LLM.
Uso, na raiz do projeto:  python -m avaliacao.avaliar_busca
"""
import json
import os
import sys

from utils.rag_utils import buscar_contexto_relevante

PERGUNTAS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "perguntas.json")


def avaliar(top_k=3):
    with open(PERGUNTAS_PATH, encoding="utf-8") as f:
        perguntas = json.load(f)

    acertos, acertos_top1, erros = 0, 0, []
    for item in perguntas:
        # Mesma função que o bot usa em produção
        trechos = buscar_contexto_relevante(item["pergunta"], top_k=top_k).split("\n---\n")
        temas = [t.split(":", 1)[0] for t in trechos]
        if item["esperado"] in temas:
            acertos += 1
            acertos_top1 += temas[0] == item["esperado"]
        else:
            erros.append({"pergunta": item["pergunta"], "esperado": item["esperado"], "veio": temas})

    n = len(perguntas)
    return {
        "n": n,
        "top_k": top_k,
        "hit_rate": acertos / n,
        "hit_rate_top1": acertos_top1 / n,
        "erros": erros,
    }


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # acentos legíveis no console do Windows
    r = avaliar(top_k=3)
    print(f"Perguntas: {r['n']}")
    print(f"Hit rate top-1: {r['hit_rate_top1']:.0%} ({round(r['hit_rate_top1'] * r['n'])}/{r['n']})")
    print(f"Hit rate top-3: {r['hit_rate']:.0%} ({round(r['hit_rate'] * r['n'])}/{r['n']})")
    for e in r["erros"]:
        print(f"  ERROU: {e['pergunta']!r} -> esperado {e['esperado']!r}, veio {e['veio']}")

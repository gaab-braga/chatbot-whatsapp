import faiss
from sentence_transformers import SentenceTransformer
import numpy as np
import os

# --- Configuração e Carregamento Inicial ---
KNOWLEDGE_BASE_PATH = "knowledge_base/documentos.md"
MODEL_NAME = 'all-MiniLM-L6-v2'

# Carrega o modelo de embedding. Este objeto é pesado e deve ser carregado apenas uma vez.
print("Carregando modelo de embedding...")
model = SentenceTransformer(MODEL_NAME)
print("Modelo carregado.")

def carregar_documentos(path):
    """Carrega e divide o documento da base de conhecimento em chunks."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        # Divide o documento por duas quebras de linha (parágrafos)
        chunks = f.read().split("\n\n")
    return [chunk.strip() for chunk in chunks if chunk.strip()]

def criar_indice_faiss(chunks):
    """Cria embeddings para os chunks e os armazena em um índice FAISS."""
    if not chunks:
        return None
    print("Criando embeddings para a base de conhecimento...")
    embeddings = model.encode(chunks)
    dimension = embeddings.shape
    index = faiss.IndexFlatL2(dimension)
    index.add(np.array(embeddings, dtype=np.float32))
    print("Índice FAISS criado com sucesso.")
    return index

# Carrega os documentos e cria o índice quando o módulo é importado
chunks_globais = carregar_documentos(KNOWLEDGE_BASE_PATH)
indice_faiss_global = criar_indice_faiss(chunks_globais)

# --- Função de Busca em Tempo de Execução ---
def buscar_contexto_relevante(query, top_k=3):
    """Busca os chunks mais relevantes para a pergunta do usuário no índice FAISS."""
    if indice_faiss_global is None or not chunks_globais:
        return ""
    
    query_embedding = model.encode([query])
    _, indices = indice_faiss_global.search(np.array(query_embedding, dtype=np.float32), top_k)
    
    contexto = "\n---\n".join([chunks_globais[i] for i in indices])
    return contexto
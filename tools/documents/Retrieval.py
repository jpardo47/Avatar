from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle

def cargar_base_vectorial(ruta_index="vector_index.faiss", ruta_metadata="metadata.pkl"):
    """Carga el índice FAISS y la metadata de los chunks."""
    index = faiss.read_index(ruta_index)
    with open(ruta_metadata, "rb") as f:
        chunks = pickle.load(f)
    return index, chunks

def buscar_respuesta(pregunta, index, chunks, modelo='paraphrase-multilingual-MiniLM-L12-v2', top_k=3):
    """Busca los fragmentos más relevantes para la pregunta."""
    model = SentenceTransformer(modelo)
    pregunta_emb = model.encode([pregunta], convert_to_numpy=True)
    _, indices = index.search(pregunta_emb, top_k)
    resultados = [chunks[i] for i in indices[0]]
    return resultados

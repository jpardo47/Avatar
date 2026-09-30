from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
import os
from LeerDocs import procesar_documento

def cargar_documentos(directorio="documentos", expandir=False):
    """Carga todos los PDFs y DOCX en una carpeta y retorna lista de chunks con metadata."""
    todos_los_chunks = []
    for archivo in os.listdir(directorio):
        if archivo.endswith(".pdf") or archivo.endswith(".docx"):
            ruta = os.path.join(directorio, archivo)
            print(f"📄 Procesando: {ruta}")
            chunks_doc = procesar_documento(ruta, expandir=expandir)
            todos_los_chunks.extend(chunks_doc)
    return todos_los_chunks

def generar_embeddings(chunks, modelo='paraphrase-multilingual-MiniLM-L12-v2'):
    """Genera embeddings para los fragmentos de texto."""
    model = SentenceTransformer(modelo)
    textos = [chunk["texto"] for chunk in chunks]
    embeddings = model.encode(textos, convert_to_numpy=True)
    return embeddings

def almacenar_en_faiss(embeddings, chunks, ruta_index="vector_index.faiss", ruta_metadata="metadata.pkl"):
    """Guarda los embeddings y metadata en archivos FAISS y Pickle."""
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)
    faiss.write_index(index, ruta_index)

    with open(ruta_metadata, "wb") as f:
        pickle.dump(chunks, f)

    print(f"✅ Base vectorial guardada con {len(chunks)} fragmentos.")

if __name__ == "__main__":
    carpeta_documentos = "documentos"
    fragmentos = cargar_documentos(carpeta_documentos)
    embeddings = generar_embeddings(fragmentos)
    almacenar_en_faiss(embeddings, fragmentos)

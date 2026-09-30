import pdfplumber
import docx
import os
import re

def extraer_texto(archivo):
    texto = ""
    extension = os.path.splitext(archivo)[1].lower()

    if extension == ".pdf":
        combined_text = []
        with pdfplumber.open(archivo) as pdf:
            for page in pdf.pages:
                plain_text = page.extract_text()
                if plain_text:
                    combined_text.append(plain_text.strip())
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        if row:
                            line = " | ".join(cell.strip() if cell else "" for cell in row)
                            combined_text.append(line)
        texto = "\n".join(combined_text)

    elif extension == ".docx":
        doc = docx.Document(archivo)
        texto = "\n".join(parrafo.text for parrafo in doc.paragraphs if parrafo.text.strip())

    else:
        raise ValueError("Formato no soportado. Usa PDF o DOCX.")

    texto = limpiar_texto(texto)
    return texto

def limpiar_texto(texto):
    texto = texto.replace('\xa0', ' ')  # Espacios no separables
    texto = re.sub(r'\s+', ' ', texto)  # Espacios múltiples
    texto = texto.strip()
    return texto

def expandir_con_sinonimos(texto):
    sinonimos = {
        "voltaje de batería": "voltaje de batería (tensión inestable, alimentación inestable, problema de energía)",
        "fracaso de alimentación": "fracaso de alimentación (problema de energía, fallo eléctrico)",
        "batería": "batería (fuente de energía, alimentación interna)",
        "alarma técnica": "alarma técnica (error, advertencia, señal de fallo)"
    }
    for original, expansion in sinonimos.items():
        texto = texto.replace(original, expansion)
    return texto

def dividir_en_chunks(texto, tamano_chunk=1000, solapamiento=200):
    oraciones = re.split(r'(?<=[.!?])\s+', texto)
    chunks = []
    chunk_actual = []
    longitud_actual = 0

    for oracion in oraciones:
        if longitud_actual + len(oracion) > tamano_chunk:
            chunks.append(" ".join(chunk_actual))
            # retrocede un poco para dar contexto
            if solapamiento > 0:
                retroceso = []
                while chunk_actual and sum(len(o) for o in retroceso) < solapamiento:
                    retroceso.insert(0, chunk_actual.pop())
                chunk_actual = retroceso
                longitud_actual = sum(len(o) for o in chunk_actual)
            else:
                chunk_actual = []
                longitud_actual = 0

        chunk_actual.append(oracion)
        longitud_actual += len(oracion)

    if chunk_actual:
        chunks.append(" ".join(chunk_actual))

    return chunks

def procesar_documento(archivo, expandir=False):
    texto = extraer_texto(archivo)
    if expandir:
        texto = expandir_con_sinonimos(texto)

    chunks = dividir_en_chunks(texto)
    metadatos_chunks = [
        {
            "texto": chunk,
            "metadata": {
                "fuente": os.path.basename(archivo),
                "chunk_id": idx
            }
        }
        for idx, chunk in enumerate(chunks)
    ]
    return metadatos_chunks

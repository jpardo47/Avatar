"""Único punto de entrada de Kaspian: python app.py."""
import os
import mimetypes
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from services.chat import answer, ProviderError

load_dotenv(Path(__file__).with_name('.env'))
mimetypes.add_type('text/javascript', '.mjs')
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024
app.config['TEMPLATES_AUTO_RELOAD'] = True

@app.get('/')
def index():
    return render_template('index.html')

@app.get('/health')
def health():
    return jsonify(status='ok', mode='online' if os.getenv('OPENROUTER_API_KEY') and os.getenv('CHAT_MODEL') else 'demo')

@app.post('/api/chat')
def chat():
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not isinstance(data.get('message'), str):
        return jsonify(error='Envía una pregunta en el campo message.'), 400
    message = data['message'].strip()
    if not message or len(message) > 2000:
        return jsonify(error='Escribe entre 1 y 2000 caracteres.'), 400
    try:
        return jsonify(answer(message))
    except ProviderError:
        return jsonify(error='No pude consultar el servicio de respuestas. Revisa la configuración o inténtalo de nuevo.'), 502

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')), debug=False)

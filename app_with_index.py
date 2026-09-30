"""Compatibilidad con el comando anterior; el servidor está en app.py."""
from app import app

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)

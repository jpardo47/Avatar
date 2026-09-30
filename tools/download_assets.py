"""Descarga las versiones fijas del visor. No sobrescribe el avatar recuperado."""
from pathlib import Path
import requests

ROOT = Path(__file__).resolve().parents[1] / 'static'
FILES = {
    'vendor/three/three.module.js': 'https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js',
    'vendor/three/addons/loaders/GLTFLoader.js': 'https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/loaders/GLTFLoader.js',
    'vendor/three/addons/utils/BufferGeometryUtils.js': 'https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/utils/BufferGeometryUtils.js',
    'vendor/three/LICENSE': 'https://cdn.jsdelivr.net/npm/three@0.169.0/LICENSE',
}
if __name__ == '__main__':
    for name, url in FILES.items():
        try:
            response = requests.get(url, timeout=40)
            response.raise_for_status()
            if name.endswith('.glb') and response.content[:4] != b'glTF':
                raise ValueError('El proveedor no devolvió un GLB válido')
            destination = ROOT / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(response.content)
            print(name, len(response.content))
        except (requests.RequestException, ValueError) as error:
            print(name, type(error).__name__)

# Kaspian · Avatar biomédico

## Iniciar en Windows

```powershell
python -m pip install -r requirements.txt
python app.py
```

Abre http://127.0.0.1:5000. No abras el HTML directamente. Después de instalar las dependencias, también puedes hacer doble clic en `iniciar.cmd`.

El proyecto funciona sin claves con respuestas locales **de demostración**, voz del navegador y el avatar original de Ready Player Me recuperado y adaptado. Pulsa **Probar voz y expresiones**. La voz necesita una voz instalada en el navegador/sistema; el reconocimiento de voz depende del navegador, de permisos y puede requerir Internet. Usa localhost o HTTPS para el micrófono.

## Inteligencia artificial opcional

Añade a tu `.env` las variables de `.env.example`: `OPENROUTER_API_KEY` y `CHAT_MODEL` (identificador de un modelo disponible en tu cuenta de OpenRouter). No reemplaces otras claves que necesites. Reinicia el servidor. Las credenciales nunca se envían al navegador. El modo activo se muestra en la cabecera. Sin proveedor configurado, las respuestas no constituyen una IA general ni consultan documentos.

Se retiró una clave que estaba incrustada en el código antiguo. Revócala en su proveedor; borrarla del archivo no la elimina del historial de Git.

## Avatar y expresiones

Se recuperó el modelo original Ready Player Me `68b4cf67bac430a52cce05e1` de la caché de Unity, al revisar las nuevas carpetas `Asistente_Virtual` y `Asistente virtual`. La copia original sin modificaciones está en `static/models/kaspian-original.glb`; el modelo preparado está en `static/models/kaspian.glb`. Ya no se utiliza el personaje construido con esferas.

La apariencia predeterminada tiene piel clara, ojos café claro, cabello lacio castaño oscuro con variante taper fade, nariz respingada y suéter beige de cuello redondo. El corte es una adaptación de la malla de cabello recuperada: no depende del antiguo catálogo ni del servicio web de Ready Player Me.

Incluye parpadeo, sonrisa, cejas para escucha/pensamiento, movimientos suaves de cabeza y apertura de boca mientras la síntesis de voz realmente está activa. La animación de labios es aproximada y temporal: no es sincronización fonética con el audio. Se detiene al finalizar, cancelar o fallar la voz. Respeta la preferencia de movimiento reducido para los movimientos de cabeza y cuerpo.

El original tenía solamente `mouthOpen` y `mouthSmile`. Se transfirió `eyesClosed` desde una plantilla RPM local verificando la correspondencia UV, y se añadieron deformaciones suaves para cejas, nariz, ancho facial y cabello. `tools/prepare_avatar.py` reproduce esa preparación (requiere numpy y la plantilla en `legacy/Asistente virtual/…`, que no se sube al repositorio). El script conserva el original y genera un nuevo GLB; no necesita Blender, Unity abierto ni llamadas externas.

## Interfaz

La página sigue el estilo «Accessible & Ethical»: cian clínico y verde salud, tipografía Figtree servida localmente y tema claro u oscuro según el sistema. El texto cumple contraste WCAG AA en ambos temas y los controles miden al menos 44 × 44 px. Hay enlace para saltar a la conversación, foco visible, iconos SVG (Lucide) y soporte para movimiento reducido. Mientras Kaspian prepara una respuesta, el chat muestra un indicador de escritura.

## Personalizar

Pulsa **Personalizar avatar**. Las pestañas **Rostro**, **Cabello** y **Ropa** permiten cambiar colores, nariz, ancho facial, corte y volumen superior. Los cambios se guardan en este navegador. **Restablecer** vuelve a la apariencia solicitada. **Exportar ajustes** e **Importar ajustes** permiten guardar y recuperar un perfil JSON; ese archivo contiene ajustes, no un modelo 3D exportado. El editor incluye tres variantes del cabello recuperado y un suéter recoloreable, no un catálogo completo de prendas.

Usa **Rostro**, **Medio cuerpo** o **Cuerpo completo** para cambiar el encuadre. Arrastra sobre el avatar o enfoca el visor y usa las flechas izquierda/derecha para girarlo. Los botones de zoom permiten acercar y alejar.

## Estructura

```text
├── app.py                  Servidor Flask: página, /health y /api/chat
├── iniciar.cmd             Arranque con doble clic en Windows
├── requirements.txt
├── .env.example            Variables opcionales (copiar a .env)
├── services/chat.py        Respuestas locales y proveedor opcional (OpenRouter)
├── templates/index.html    Interfaz principal
├── static/
│   ├── css/app.css         Estilos y tokens de diseño (claro/oscuro)
│   ├── js/                 Conversación y voz (app.js), visor 3D (avatar-view.js),
│   │                       editor (editor.js) y validación de perfiles (settings.mjs)
│   ├── models/             Avatar original recuperado y versión con expresiones
│   └── vendor/             Three.js 0.169.0 (MIT) y fuente Figtree (OFL)
├── tests/                  Pruebas del servidor, del modelo y de los ajustes
├── tools/                  Preparación del avatar y descarga de dependencias
└── docs/                   Documentación original y registro de la recuperación
```

La carpeta `legacy/` (proyectos Unity antiguos, con la plantilla que usa `tools/prepare_avatar.py`) se conserva solo en local y está excluida en `.gitignore`.

Se eliminaron servidores duplicados, clientes de voz de escritorio, integración de Telegram desconectada, la plantilla de pizzería, el bot anterior, el ZIP de GPTAvatar y las cachés de Unity.

## Verificación

```powershell
python -m unittest discover -s tests -v
node tests/test_settings.mjs
```

En el navegador: probar voz, detener a mitad de frase, enviar una pregunta, desactivar voz, negar micrófono y comprobar tamaño móvil. El avatar y Three.js no necesitan servicios externos. Las llamadas al proveedor de IA tienen un límite de tiempo y muestran errores recuperables.

Referencias de implementación: https://threejs.org/docs/pages/GLTFLoader.html y https://threejs.org/docs/pages/Mesh.html.

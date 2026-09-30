# Recuperación y adaptación de Kaspian

La segunda revisión encontró proyectos Unity en `Asistente_Virtual/Avatar` y `Asistente virtual/Asistente_Diagnostico`. El script `LoadAvatar.cs` confirmó el identificador `68b4cf67bac430a52cce05e1`.

El GLB original se recuperó del caché local de Unity en `%USERPROFILE%/AppData/LocalLow/DefaultCompany/Avatar/Ready Player Me/Avatars/68b4cf67bac430a52cce05e1/2fac66e374c947c41bc74325c6e3d934/68b4cf67bac430a52cce05e1.glb`. Se guardó sin modificar como `static/models/kaspian-original.glb`.

El archivo original contiene rig, texturas, ropa y los controles `mouthOpen` y `mouthSmile`. No contiene parpadeo. Se recuperó el control `eyesClosed` de `Assets/Samples/Ready Player Me Core/7.4.0/QuickStart/PreviewAvatar/PreviewMesh.glb`, verificando correspondencias UV en cada malla facial antes de transferir desplazamientos. Se conserva la licencia del paquete de la plantilla en esta carpeta.

La versión `static/models/kaspian.glb` añade parpadeo, cejas, nariz respingada, ancho facial y variantes del cabello. Se eliminaron geométricamente la capucha y los cordones conservando el cuerpo de la prenda y se reconstruyó el borde del cuello. Los colores, el degradado del cabello y el tejido se aplican mediante materiales del visor; no se modifican las texturas originales.

El editor local no depende de la disponibilidad del sitio Ready Player Me. Ofrece los rasgos y variantes incluidos, no el catálogo completo del antiguo creador. La exportación de ajustes es un perfil JSON que se aplica junto al GLB local.

El ZIP GPTAvatar conserva otros modelos Unity (Seth y Teacher); no se usaron para esta adaptación porque fue posible recuperar Kaspian.

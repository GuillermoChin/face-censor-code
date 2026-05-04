🎭 face-censor-code
Sistema automático de censura facial para imágenes y videos.
Detecta rostros con MediaPipe y aplica el método de censura que elijas: desenfoque, pixelado o sticker personalizado.

Desarrollado como proyecto educativo de código abierto para su uso en clases de visión computacional y programación modular en Python.

Autor: Guillermo Chin — "el chico de las estrellas"
Institución: ITESCAM | Campeche, México
Licencia: MIT

📋 Tabla de contenidos

¿Qué hace este proyecto?
Estructura del proyecto
Requisitos
Instalación
Uso
Métodos de censura
Arquitectura del sistema
Conceptos educativos cubiertos
Personalización
Contribuciones
Créditos y citación
Licencia


✨ ¿Qué hace este proyecto?

Escanea automáticamente la carpeta /entradas buscando imágenes y videos.
Detecta todos los rostros presentes usando MediaPipe Face Detection.
Aplica la censura elegida sobre cada cara detectada.
Guarda el resultado en /salida con el mismo nombre del archivo original.
Evita reprocesar archivos que ya existen en /salida.

Todo sin configuración adicional: solo coloca tus archivos y ejecuta python main.py.

🗂️ Estructura del proyecto
face-censor-code/
│
├── entradas/                  # 📥 Coloca aquí tus imágenes y videos
├── salida/                    # 📤 Aquí aparecen los archivos procesados
├── recursos/                  # 🎨 Stickers PNG para el método overlay
│
├── src/                       # 🧩 Módulos del sistema
│   ├── __init__.py
│   ├── detector.py            # Detección facial con MediaPipe
│   ├── censores.py            # Métodos: blur, pixelado, sticker
│   ├── procesador_video.py    # Pipeline para videos
│   ├── procesador_imagen.py   # Pipeline para imágenes
│   └── utils.py               # Escaneo, verificación y mensajes
│
├── main.py                    # ▶️  Punto de entrada principal
├── config.py                  # ⚙️  Configuración global
├── requirements.txt           # 📦 Dependencias
└── README.md                  # 📖 Este archivo

🖥️ Requisitos

Python 3.9 o superior
pip
Sistema operativo: Windows, macOS o Linux


🚀 Instalación
1. Clonar el repositorio
git clone https://github.com/GuillermoChin/face-censor-code.git
cd face-censor-code
2. Crear entorno virtual (recomendado)
# Windows
python -m venv venv
venv\Scripts\activate

# Mac / Linux
python -m venv venv
source venv/bin/activate
3. Instalar dependencias
pip install -r requirements.txt

▶️ Uso
Paso 1 — Agrega tus archivos
Coloca las imágenes y/o videos que quieras censurar en la carpeta /entradas:
entradas/
├── foto_evento.jpg
├── retrato.png
└── video_conferencia.mp4
Paso 2 — Ejecuta el sistema
python main.py
Paso 3 — Elige el método de censura
── MÉTODO DE CENSURA ──────────────────────
  [1] blur      → Desenfoque gaussiano
  [2] pixelado  → Efecto mosaico
  [3] sticker   → Superponer imagen PNG

  Elige una opción (1/2/3): 2
Paso 4 — Recoge tu resultado
Los archivos procesados aparecen en /salida con el mismo nombre original.

🎨 Métodos de censura
MétodoDescripciónParámetro ajustable en config.pyblurDesenfoque gaussiano suaveBLUR_INTENSIDAD (default: 99)pixeladoEfecto mosaico retroPIXEL_BLOQUE (default: 20)stickerPNG personalizado con transparenciaArchivos en /recursos
Usando stickers personalizados
Coloca cualquier archivo .png (con transparencia recomendada) en la carpeta /recursos:
recursos/
├── emoji_star.png
├── censored_bar.png
└── sticker_default.png
Al elegir el método sticker, el sistema te mostrará la lista de PNGs disponibles para elegir.

Tip: Usa imágenes PNG con fondo transparente (canal alfa) para mejores resultados. Puedes crearlas en remove.bg o en cualquier editor de imagen.


🏗️ Arquitectura del sistema
El sistema sigue una arquitectura de pipeline modular:
main.py  (orquestador)
   │
   ├── config.py          ← parámetros globales
   ├── utils.py           ← escaneo y verificación de archivos
   │
   ├── detector.py        ← detección facial (MediaPipe)
   ├── censores.py        ← aplicación de censura
   │
   ├── procesador_imagen.py  ← pipeline para imágenes
   └── procesador_video.py   ← pipeline frame a frame para video
Cada módulo tiene una única responsabilidad siguiendo el principio SRP (Single Responsibility Principle). Esto facilita:

Modificar un método sin afectar los demás
Probar cada módulo de forma independiente
Reutilizar módulos en otros proyectos

Probar módulos individualmente
# Probar solo la detección facial
python src/detector.py entradas/foto.jpg

# Probar un método de censura directamente
python src/censores.py entradas/foto.jpg pixelado

# Procesar una sola imagen sin el menú
python src/procesador_imagen.py entradas/foto.jpg blur

# Procesar un solo video sin el menú
python src/procesador_video.py entradas/clip.mp4 sticker emoji.png

📚 Conceptos educativos cubiertos
Este proyecto fue diseñado para ilustrar los siguientes conceptos en clase:
Visión computacional
ConceptoDónde se implementaDetección facial con redes neuronalesdetector.pyBounding box y coordenadas normalizadasdetector.py → detectar_caras()ROI (Region of Interest)censores.py → todos los métodosFiltro gaussianocensores.py → aplicar_blur()Interpolación de imágenescensores.py → aplicar_pixel()Composición alfa (alpha compositing)censores.py → aplicar_sticker()Pipeline de video frame a frameprocesador_video.pyCódecs y FourCCprocesador_video.py → crear_writer()
Programación en Python
ConceptoDónde se implementaArquitectura modularToda la estructura del proyectoPrincipio SRPSeparación en módulos especializadosPatrón Strategycensores.py → aplicar_censura()Context managers (with)Uso de MediaPipe y recursosGeneradores (yield)procesador_video.py → _iterar_frames()Manejo de errores con try/finallyprocesador_video.pyBatch processingprocesar_lote_imagenes/videos()Validación de entrada de usuariomain.py → menu_metodo()

⚙️ Personalización
Todos los parámetros ajustables están centralizados en config.py:
# Intensidad del desenfoque (debe ser impar)
BLUR_INTENSIDAD = 99

# Tamaño del bloque de pixelado (en píxeles)
PIXEL_BLOQUE = 20

# Margen extra alrededor de la cara detectada
MARGEN_CARA = 20

# Confianza mínima de detección (0.0 a 1.0)
DETECCION_CONFIANZA_MINIMA = 0.5
Agregar un nuevo método de censura

Agrega una función aplicar_mi_metodo(frame, caras) en censores.py
Registra el nombre en METODOS_VALIDOS dentro de config.py
Agrega el caso en aplicar_censura() dentro de censores.py
Actualiza el menú en main.py → menu_metodo()


🤝 Contribuciones
¡Las contribuciones son bienvenidas! Si quieres mejorar el proyecto:

Haz un fork del repositorio
Crea una rama para tu mejora: git checkout -b feature/mi-mejora
Haz commit de tus cambios: git commit -m "feat: descripción de la mejora"
Haz push a tu rama: git push origin feature/mi-mejora
Abre un Pull Request

Ideas para contribuir

 Soporte para procesamiento en paralelo con multiprocessing
 Interfaz gráfica con Tkinter o PyQt
 Exportar video con códec H.264
 Modo línea de comandos con argparse
 Soporte para streams de cámara en tiempo real


📄 Créditos y citación
Si usas este proyecto en clases, trabajos académicos o proyectos derivados, por favor incluye la siguiente atribución:
Chin, G. (2025). face-censor-code: Sistema automático de censura facial
con MediaPipe y OpenCV [Software educativo].
ITESCAM, Campeche, México.
https://github.com/GuillermoChin/face-censor-code

📜 Licencia
Este proyecto está publicado bajo la licencia MIT.
Puedes usarlo, modificarlo y distribuirlo libremente,
siempre que mantengas la atribución al autor original.

<p align="center">
  Hecho con 💙 desde Campeche, México<br>
  <em>"el chico de las estrellas"</em>
</p>
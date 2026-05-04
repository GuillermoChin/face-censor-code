# ============================================================
#  face-censor-code | Módulo: config.py
#  Autor: Guillermo Chin — "el chico de las estrellas"
#  Institución: ITESCAM | Campeche, México
#  GitHub: https://github.com/GuillermoChin/face-censor-code
#  Licencia: MIT — Libre uso con atribución
# ------------------------------------------------------------
#  DESCRIPCIÓN:
#  Archivo de configuración global del proyecto.
#  Aquí se definen todas las rutas, parámetros y constantes
#  que los demás módulos utilizan. Si necesitas adaptar el
#  proyecto a tu entorno, este es el único archivo que debes
#  modificar en la mayoría de los casos.
# ============================================================

import os

# ─────────────────────────────────────────────
#  RUTAS PRINCIPALES
#  Todas las rutas son relativas a la raíz del proyecto.
#  Puedes cambiarlas a rutas absolutas si lo necesitas.
# ─────────────────────────────────────────────

# Carpeta donde el usuario coloca los archivos a procesar
RUTA_ENTRADAS = "entradas"

# Carpeta donde se guardan los archivos ya censurados
RUTA_SALIDA = "salida"

# Carpeta donde se colocan los stickers/overlays disponibles
RUTA_RECURSOS = "recursos"


# ─────────────────────────────────────────────
#  FORMATOS SOPORTADOS
#  El sistema detecta automáticamente el tipo de archivo
#  según su extensión. Agrega o quita extensiones aquí.
# ─────────────────────────────────────────────

# Extensiones reconocidas como imagen
EXTENSIONES_IMAGEN = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Extensiones reconocidas como video
EXTENSIONES_VIDEO = {".mp4", ".avi", ".mov", ".mkv", ".wmv"}


# ─────────────────────────────────────────────
#  MÉTODOS DE CENSURA DISPONIBLES
#  Estos valores son los que el usuario puede elegir
#  en el menú principal (main.py).
# ─────────────────────────────────────────────

METODO_BLUR    = "blur"      # Desenfoque gaussiano
METODO_PIXEL   = "pixelado"  # Efecto mosaico/pixelado
METODO_STICKER = "sticker"   # Superponer imagen desde /recursos

# Lista de métodos válidos (usada para validar la elección del usuario)
METODOS_VALIDOS = [METODO_BLUR, METODO_PIXEL, METODO_STICKER]


# ─────────────────────────────────────────────
#  PARÁMETROS DE CENSURA
#  Ajusta estos valores para cambiar la intensidad
#  o apariencia de cada método de censura.
# ─────────────────────────────────────────────

# Intensidad del desenfoque gaussiano (debe ser impar: 51, 71, 99...)
# A mayor valor, mayor desenfoque
BLUR_INTENSIDAD = 99

# Tamaño del bloque de pixelado (en píxeles)
# A mayor valor, cuadros más grandes (más pixelado)
PIXEL_BLOQUE = 20

# Nombre por defecto del sticker si el usuario no especifica uno
# El archivo debe existir dentro de RUTA_RECURSOS
STICKER_DEFECTO = "sticker_default.png"

# Margen extra (en píxeles) alrededor de la cara detectada
# Útil para que la censura cubra bien la cabeza completa
MARGEN_CARA = 20


# ─────────────────────────────────────────────
#  CONFIGURACIÓN DE VIDEO
# ─────────────────────────────────────────────

# Códec de video para la salida (mp4v es compatible con .mp4)
# Alternativas: XVID (.avi), avc1 (H.264, requiere compilación especial)
VIDEO_CODEC = "mp4v"

# Extensión del video de salida
VIDEO_EXTENSION_SALIDA = ".mp4"


# ─────────────────────────────────────────────
#  CONFIGURACIÓN DE DETECCIÓN FACIAL (MediaPipe)
#  Referencia: https://developers.google.com/mediapipe
# ─────────────────────────────────────────────

# Confianza mínima para considerar una detección como válida (0.0 a 1.0)
# Valores más altos = menos falsas detecciones, pero puede perder caras
DETECCION_CONFIANZA_MINIMA = 0.5

# Si es True, el detector reutiliza el modelo entre frames (más rápido en video)
DETECCION_MODO_VIDEO = True


# ─────────────────────────────────────────────
#  MENSAJES DEL SISTEMA
#  Centralizar los mensajes facilita traducirlos o modificarlos
# ─────────────────────────────────────────────

MSG_YA_EXISTE_VIDEO  = "⚠️  Este video ya existe en salida: {nombre} — se omitirá."
MSG_YA_EXISTE_IMAGEN = "⚠️  Esta imagen ya existe en salida: {nombre} — se omitirá."
MSG_NO_CARA          = "ℹ️  No se detectaron caras en: {nombre}"
MSG_PROCESANDO       = "🔄  Procesando: {nombre}"
MSG_LISTO            = "✅  Guardado en salida: {nombre}"
MSG_TIPO_INVALIDO    = "⛔  Archivo no soportado (se omitirá): {nombre}"
MSG_METODO_INVALIDO  = "⛔  Método no válido. Elige entre: {metodos}"


# ─────────────────────────────────────────────
#  FUNCIÓN DE VALIDACIÓN DE RUTAS
#  Verifica que las carpetas necesarias existan al arrancar.
#  Si no existen, las crea automáticamente.
# ─────────────────────────────────────────────

def verificar_estructura():
    """
    Verifica y crea (si no existen) las carpetas del proyecto.
    Se llama automáticamente desde main.py al iniciar el sistema.
    """
    for ruta in [RUTA_ENTRADAS, RUTA_SALIDA, RUTA_RECURSOS]:
        if not os.path.exists(ruta):
            os.makedirs(ruta)
            print(f"📁 Carpeta creada automáticamente: {ruta}/")
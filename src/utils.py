# ============================================================
#  face-censor-code | Módulo: utils.py
#  Autor: Guillermo Chin — "el chico de las estrellas"
#  Institución: ITESCAM | Campeche, México
#  GitHub: https://github.com/GuillermoChin/face-censor-code
#  Licencia: MIT — Libre uso con atribución
# ------------------------------------------------------------
#  DESCRIPCIÓN:
#  Módulo de utilidades generales del sistema.
#  Contiene funciones para:
#    - Escanear la carpeta de entradas
#    - Clasificar archivos por tipo (imagen/video/desconocido)
#    - Verificar si un archivo ya fue procesado
#    - Construir rutas de salida
#    - Mostrar mensajes formateados en consola
#
#  Este módulo NO realiza procesamiento de imagen ni video.
#  Solo maneja lógica de archivos y mensajes del sistema.
#  Es el primer eslabón del pipeline.
# ============================================================

import os
from config import (
    RUTA_ENTRADAS,
    RUTA_SALIDA,
    EXTENSIONES_IMAGEN,
    EXTENSIONES_VIDEO,
    VIDEO_EXTENSION_SALIDA,
    MSG_YA_EXISTE_VIDEO,
    MSG_YA_EXISTE_IMAGEN,
    MSG_TIPO_INVALIDO,
)


# ─────────────────────────────────────────────
#  CLASIFICACIÓN DE ARCHIVOS
# ─────────────────────────────────────────────

def obtener_tipo(ruta_archivo):
    """
    Determina si un archivo es imagen, video o no soportado.

    Parámetros:
        ruta_archivo (str): Ruta completa o nombre del archivo.

    Retorna:
        str: "imagen", "video" o "desconocido"

    Ejemplo:
        >>> obtener_tipo("foto.jpg")
        'imagen'
        >>> obtener_tipo("clip.mp4")
        'video'
        >>> obtener_tipo("documento.pdf")
        'desconocido'
    """
    # Extraemos solo la extensión y la ponemos en minúsculas
    # para que ".JPG" y ".jpg" se traten igual
    _, extension = os.path.splitext(ruta_archivo)
    extension = extension.lower()

    if extension in EXTENSIONES_IMAGEN:
        return "imagen"
    elif extension in EXTENSIONES_VIDEO:
        return "video"
    else:
        return "desconocido"


# ─────────────────────────────────────────────
#  ESCANEO DE LA CARPETA DE ENTRADAS
# ─────────────────────────────────────────────

def escanear_entradas():
    """
    Lee todos los archivos dentro de la carpeta de entradas
    y los clasifica en imágenes, videos y archivos no soportados.

    No es recursivo: solo analiza el nivel raíz de /entradas.
    Los archivos .gitkeep se ignoran automáticamente.

    Retorna:
        dict con tres listas:
            {
                "imagenes":     [lista de rutas absolutas],
                "videos":       [lista de rutas absolutas],
                "desconocidos": [lista de rutas absolutas]
            }

    Ejemplo de uso:
        archivos = escanear_entradas()
        for ruta in archivos["videos"]:
            print(ruta)
    """
    resultado = {
        "imagenes":     [],
        "videos":       [],
        "desconocidos": []
    }

    # Verificar que la carpeta de entradas existe
    if not os.path.exists(RUTA_ENTRADAS):
        print(f"⛔  La carpeta '{RUTA_ENTRADAS}' no existe. Ejecuta main.py para crearla.")
        return resultado

    # Iterar sobre todos los archivos en la carpeta
    for nombre_archivo in os.listdir(RUTA_ENTRADAS):

        # Ignorar archivos ocultos y marcadores de Git
        if nombre_archivo.startswith(".") or nombre_archivo == ".gitkeep":
            continue

        ruta_completa = os.path.join(RUTA_ENTRADAS, nombre_archivo)

        # Solo procesar archivos, no subcarpetas
        if not os.path.isfile(ruta_completa):
            continue

        tipo = obtener_tipo(nombre_archivo)
        resultado[tipo + "s"].append(ruta_completa)

    return resultado


# ─────────────────────────────────────────────
#  VERIFICACIÓN DE EXISTENCIA EN SALIDA
# ─────────────────────────────────────────────

def construir_ruta_salida(ruta_entrada, tipo):
    """
    Genera la ruta de salida correspondiente a un archivo de entrada.

    Para videos, siempre genera un .mp4 (definido en config.py).
    Para imágenes, conserva la extensión original.

    Parámetros:
        ruta_entrada (str): Ruta del archivo en /entradas
        tipo (str):         "imagen" o "video"

    Retorna:
        str: Ruta completa del archivo de salida esperado.

    Ejemplo:
        >>> construir_ruta_salida("entradas/video.avi", "video")
        'salida/video.mp4'
        >>> construir_ruta_salida("entradas/foto.jpg", "imagen")
        'salida/foto.jpg'
    """
    nombre_base = os.path.basename(ruta_entrada)       # "video.avi"
    nombre_sin_ext, extension = os.path.splitext(nombre_base)

    if tipo == "video":
        # Los videos de salida siempre son .mp4
        nombre_salida = nombre_sin_ext + VIDEO_EXTENSION_SALIDA
    else:
        # Las imágenes conservan su extensión original
        nombre_salida = nombre_base

    return os.path.join(RUTA_SALIDA, nombre_salida)


def ya_fue_procesado(ruta_entrada, tipo):
    """
    Verifica si el archivo ya fue procesado consultando /salida.

    Si existe, imprime un mensaje informativo y retorna True.
    Si no existe, retorna False y el procesamiento continúa.

    Parámetros:
        ruta_entrada (str): Ruta del archivo original en /entradas
        tipo (str):         "imagen" o "video"

    Retorna:
        bool: True si ya existe en salida, False si no.

    Ejemplo de uso:
        if ya_fue_procesado("entradas/clip.mp4", "video"):
            continue   # saltamos al siguiente archivo
    """
    ruta_salida = construir_ruta_salida(ruta_entrada, tipo)
    nombre = os.path.basename(ruta_salida)

    if os.path.exists(ruta_salida):
        if tipo == "video":
            print(MSG_YA_EXISTE_VIDEO.format(nombre=nombre))
        else:
            print(MSG_YA_EXISTE_IMAGEN.format(nombre=nombre))
        return True

    return False


# ─────────────────────────────────────────────
#  MENSAJES Y FORMATO DE CONSOLA
# ─────────────────────────────────────────────

def imprimir_separador(titulo=""):
    """
    Imprime una línea separadora para organizar la salida en consola.
    Útil para separar visualmente cada archivo procesado.

    Parámetros:
        titulo (str): Texto opcional que aparece en el centro.

    Ejemplo:
        imprimir_separador("PROCESANDO VIDEOS")
        # ──────────── PROCESANDO VIDEOS ────────────
    """
    ancho = 50
    if titulo:
        print(f"\n{'─' * 10} {titulo} {'─' * 10}\n")
    else:
        print("─" * ancho)


def imprimir_resumen(procesados, omitidos, errores):
    """
    Muestra un resumen final al terminar el procesamiento de todos
    los archivos.

    Parámetros:
        procesados (int): Archivos procesados correctamente.
        omitidos   (int): Archivos que ya existían en /salida.
        errores    (int): Archivos que fallaron durante el proceso.
    """
    imprimir_separador("RESUMEN FINAL")
    print(f"  ✅  Procesados correctamente : {procesados}")
    print(f"  ⚠️   Omitidos (ya existían)   : {omitidos}")
    print(f"  ❌  Con errores              : {errores}")
    imprimir_separador()


# ─────────────────────────────────────────────
#  LISTADO DE STICKERS DISPONIBLES
# ─────────────────────────────────────────────

def listar_stickers(ruta_recursos):
    """
    Escanea la carpeta de recursos y devuelve los archivos PNG
    disponibles como stickers.

    Parámetros:
        ruta_recursos (str): Ruta a la carpeta /recursos

    Retorna:
        list: Lista de nombres de archivo .png encontrados.
              Retorna lista vacía si la carpeta no existe o está vacía.

    Ejemplo de uso:
        stickers = listar_stickers("recursos")
        # ["emoji_star.png", "sticker_default.png"]
    """
    if not os.path.exists(ruta_recursos):
        return []

    return [
        archivo
        for archivo in os.listdir(ruta_recursos)
        if archivo.lower().endswith(".png") and not archivo.startswith(".")
    ]
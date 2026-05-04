# ============================================================
#  face-censor-code | Módulo: procesador_video.py
#  Autor: Guillermo Chin — "el chico de las estrellas"
#  Institución: ITESCAM | Campeche, México
#  GitHub: https://github.com/GuillermoChin/face-censor-code
#  Licencia: MIT — Libre uso con atribución
# ------------------------------------------------------------
#  DESCRIPCIÓN:
#  Módulo encargado del pipeline completo de procesamiento
#  para archivos de video.
#
#  A diferencia de las imágenes, un video es una secuencia
#  de frames (fotogramas). Este módulo:
#    1. Abre el video con OpenCV (VideoCapture)
#    2. Lee sus propiedades: FPS, resolución, total de frames
#    3. Crea el archivo de salida (VideoWriter)
#    4. Itera frame por frame aplicando detección + censura
#    5. Escribe cada frame procesado en el video de salida
#    6. Muestra barra de progreso con tqdm
#    7. Cierra correctamente todos los recursos al terminar
#
#  CONCEPTOS CLAVE para estudiantes:
#  - FPS (Frames Per Second): cantidad de fotogramas por segundo.
#    Un video de 30 FPS tiene 30 imágenes por cada segundo de video.
#  - VideoCapture: objeto de OpenCV que abre y lee un video.
#  - VideoWriter: objeto de OpenCV que crea y escribe un video.
#  - Códec (codec): algoritmo de compresión/descompresión de video.
#    Ej: mp4v, XVID, H264. Define cómo se almacenan los frames.
#  - FourCC: código de 4 caracteres que identifica el códec.
#    cv2.VideoWriter_fourcc(*'mp4v') crea el código para MP4.
#  - tqdm: biblioteca que genera barras de progreso en consola.
#    Muy útil en procesos largos para estimar tiempo restante.
# ============================================================

import cv2
import os
import sys

# tqdm provee la barra de progreso en consola
# Importación defensiva: si no está instalada, usamos un reemplazo simple
try:
    from tqdm import tqdm
    TQDM_DISPONIBLE = True
except ImportError:
    TQDM_DISPONIBLE = False
    print("⚠️  tqdm no instalado. Sin barra de progreso.")
    print("   Instala con: pip install tqdm")

# Asegurar que Python encuentre los módulos del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "src"))

from detector import crear_detector, detectar_caras
from censores import aplicar_censura
from config import (
    VIDEO_CODEC,
    VIDEO_EXTENSION_SALIDA,
    MSG_PROCESANDO,
    MSG_LISTO,
    MSG_NO_CARA,
)
from utils import construir_ruta_salida


# ─────────────────────────────────────────────
#  LECTURA DE PROPIEDADES DEL VIDEO
# ─────────────────────────────────────────────

def obtener_propiedades(cap):
    """
    Extrae las propiedades técnicas de un VideoCapture abierto.

    OpenCV representa las propiedades de un video como constantes
    numéricas (CAP_PROP_*). Esta función las agrupa en un
    diccionario legible para usar en el resto del pipeline.

    Parámetros:
        cap (cv2.VideoCapture): Objeto de captura ya abierto.

    Retorna:
        dict con las propiedades del video:
            {
                "fps"        : float → fotogramas por segundo,
                "ancho"      : int   → ancho en píxeles,
                "alto"       : int   → alto en píxeles,
                "total_frames": int  → número total de fotogramas,
                "duracion_seg": float → duración en segundos
            }

    NOTA EDUCATIVA — ¿Por qué float en fps?
        La mayoría de los videos tienen FPS exactos (24, 30, 60),
        pero algunos tienen valores como 29.97 (NTSC americano)
        o 23.976. OpenCV siempre retorna FPS como float.

    Ejemplo de uso:
        cap = cv2.VideoCapture("video.mp4")
        props = obtener_propiedades(cap)
        print(props["fps"])           # → 30.0
        print(props["total_frames"])  # → 900 (30 seg a 30fps)
    """
    fps           = cap.get(cv2.CAP_PROP_FPS)
    ancho         = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    alto          = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duracion_seg  = total_frames / fps if fps > 0 else 0

    return {
        "fps":          fps,
        "ancho":        ancho,
        "alto":         alto,
        "total_frames": total_frames,
        "duracion_seg": duracion_seg,
    }


# ─────────────────────────────────────────────
#  CREACIÓN DEL WRITER DE SALIDA
# ─────────────────────────────────────────────

def crear_writer(ruta_salida, props):
    """
    Crea el objeto VideoWriter para escribir el video de salida.

    VideoWriter necesita cuatro parámetros para inicializarse:
        1. Ruta del archivo de salida
        2. FourCC: código del códec de compresión
        3. FPS: mismos que el video original
        4. Tamaño: (ancho, alto) en píxeles

    Parámetros:
        ruta_salida (str):  Ruta donde se guardará el video.
        props       (dict): Diccionario de obtener_propiedades().

    Retorna:
        cv2.VideoWriter: Objeto escritor listo para recibir frames.

    NOTA EDUCATIVA — FourCC y códecs:
        FourCC (Four Character Code) identifica el códec de video.
        cv2.VideoWriter_fourcc(*'mp4v') desempaqueta el string
        'mp4v' en 4 caracteres individuales que la función espera.
        Es equivalente a escribir:
        cv2.VideoWriter_fourcc('m', 'p', '4', 'v')

    Ejemplo de uso:
        writer = crear_writer("salida/video.mp4", props)
        writer.write(frame)   # escribir un frame
        writer.release()      # cerrar al terminar
    """
    # FourCC identifica el códec. VIDEO_CODEC viene de config.py ("mp4v")
    fourcc = cv2.VideoWriter_fourcc(*VIDEO_CODEC)

    writer = cv2.VideoWriter(
        ruta_salida,
        fourcc,
        props["fps"],
        (props["ancho"], props["alto"])
    )

    return writer


# ─────────────────────────────────────────────
#  ITERADOR DE FRAMES CON BARRA DE PROGRESO
# ─────────────────────────────────────────────

def _iterar_frames(cap, total_frames, nombre):
    """
    Generador que itera sobre los frames de un VideoCapture.

    Un generador (yield) es una función que produce valores
    uno a la vez sin cargar todo en memoria. Esto es importante
    para videos largos: no cargamos todos los frames a la vez,
    sino que procesamos uno, lo descartamos, y leemos el siguiente.

    Con tqdm disponible muestra una barra de progreso como:
        foto.mp4: 45%|████████░░░░│ 450/1000 [00:12<00:15, 30.1fps]

    Parámetros:
        cap          (cv2.VideoCapture): Video abierto.
        total_frames (int): Total de frames del video.
        nombre       (str): Nombre del archivo (para la barra).

    Yields:
        tuple (int, numpy.ndarray): (número_de_frame, frame_BGR)

    NOTA EDUCATIVA — Generadores en Python:
        La palabra clave "yield" convierte una función en generador.
        En lugar de retornar todos los valores a la vez (return),
        los produce de uno en uno bajo demanda.
        Esto hace que el uso de memoria sea O(1) respecto al
        número de frames, en lugar de O(n).
    """
    # Configurar iterador: con o sin barra según disponibilidad de tqdm
    if TQDM_DISPONIBLE:
        iterador = tqdm(
            range(total_frames),
            desc=f"   🎬 {nombre}",
            unit="frame",
            ncols=80,
            colour="cyan"
        )
    else:
        iterador = range(total_frames)

    numero_frame = 0

    for _ in iterador:
        # cap.read() retorna (éxito, frame)
        # Si ret es False, el video terminó o hubo un error de lectura
        ret, frame = cap.read()

        if not ret:
            # El video terminó antes de lo esperado
            # (puede pasar con archivos corruptos o metadatos incorrectos)
            break

        yield numero_frame, frame
        numero_frame += 1


# ─────────────────────────────────────────────
#  PIPELINE PRINCIPAL DE VIDEO
# ─────────────────────────────────────────────

def procesar_video(ruta_entrada, metodo, nombre_sticker=None):
    """
    Ejecuta el pipeline completo de censura sobre un video.

    Pasos internos:
        1. Abrir el video con VideoCapture
        2. Leer propiedades (fps, resolución, total de frames)
        3. Construir ruta de salida y crear VideoWriter
        4. Crear detector MediaPipe en modo video (reutiliza tracking)
        5. Iterar frame a frame:
            a. Detectar caras en el frame actual
            b. Aplicar censura si hay caras
            c. Escribir frame (censurado o sin cambios) en el writer
        6. Liberar VideoCapture y VideoWriter
        7. Retornar True si todo salió bien

    Parámetros:
        ruta_entrada   (str): Ruta completa al video en /entradas.
        metodo         (str): "blur", "pixelado" o "sticker".
        nombre_sticker (str, opcional): PNG en /recursos.

    Retorna:
        bool:
            True  → video procesado y guardado correctamente.
            False → error en apertura, lectura o escritura.

    NOTA EDUCATIVA — ¿Por qué liberar recursos con release()?
        VideoCapture y VideoWriter mantienen handles (manejadores)
        al sistema de archivos y a la memoria del códec.
        Si no los liberamos con .release(), el archivo de salida
        puede quedar incompleto o corrupto, y el archivo de entrada
        puede quedar bloqueado para otras aplicaciones.
        El bloque try/finally garantiza la liberación incluso si
        ocurre un error en medio del procesamiento.

    Ejemplo de uso:
        exito = procesar_video("entradas/clip.mp4", "pixelado")
        exito = procesar_video("entradas/entrevista.mp4", "sticker", "emoji.png")
    """
    nombre = os.path.basename(ruta_entrada)
    print(MSG_PROCESANDO.format(nombre=nombre))

    # ── Paso 1: Abrir el video ─────────────────────────────────────
    cap = cv2.VideoCapture(ruta_entrada)

    if not cap.isOpened():
        print(f"❌  No se pudo abrir el video: {nombre}")
        print("    Verifica que el archivo no esté corrupto o en uso.")
        return False

    # ── Paso 2: Leer propiedades ───────────────────────────────────
    props = obtener_propiedades(cap)

    print(f"   📐  Resolución  : {props['ancho']}x{props['alto']} px")
    print(f"   🎞️   FPS         : {props['fps']:.2f}")
    print(f"   🔢  Total frames: {props['total_frames']}")
    print(f"   ⏱️   Duración    : {props['duracion_seg']:.1f} seg")

    # ── Paso 3: Crear writer de salida ─────────────────────────────
    ruta_salida = construir_ruta_salida(ruta_entrada, "video")
    writer = crear_writer(ruta_salida, props)

    if not writer.isOpened():
        print(f"❌  No se pudo crear el archivo de salida: {ruta_salida}")
        cap.release()
        return False

    # ── Paso 4 a 6: Procesar frame por frame ──────────────────────
    # try/finally garantiza que cap y writer se liberen siempre,
    # incluso si ocurre una excepción en el procesamiento
    frames_con_cara  = 0
    frames_sin_cara  = 0

    try:
        # Detector en modo video: reutiliza información entre frames
        # lo que mejora la consistencia del tracking y el rendimiento
        with crear_detector(modo_video=True) as detector:

            for numero_frame, frame in _iterar_frames(
                cap, props["total_frames"], nombre
            ):
                # ── Detectar caras en este frame ──────────────────
                # DESPUÉS
                caras = detectar_caras(frame, detector, numero_frame, props["fps"])

                if caras:
                    # ── Aplicar censura y contar ───────────────────
                    frame_procesado = aplicar_censura(
                        frame, caras, metodo, nombre_sticker
                    )
                    frames_con_cara += 1
                else:
                    # Sin caras: escribir frame original sin modificar
                    frame_procesado = frame
                    frames_sin_cara += 1

                # ── Escribir frame al video de salida ─────────────
                writer.write(frame_procesado)

    finally:
        # ── Paso 6: Liberar recursos siempre ──────────────────────
        # Independientemente de si hubo error o no
        cap.release()
        writer.release()

    # ── Paso 7: Reporte de resultados ─────────────────────────────
    total = frames_con_cara + frames_sin_cara

    if frames_con_cara == 0:
        print(MSG_NO_CARA.format(nombre=nombre))
    else:
        porcentaje = (frames_con_cara / total * 100) if total > 0 else 0
        print(f"   👤  Frames con cara : {frames_con_cara} ({porcentaje:.1f}%)")
        print(f"   ⬜  Frames sin cara : {frames_sin_cara}")

    print(MSG_LISTO.format(nombre=os.path.basename(ruta_salida)))
    return True


# ─────────────────────────────────────────────
#  PROCESAMIENTO POR LOTE DE VIDEOS
# ─────────────────────────────────────────────

def procesar_lote_videos(lista_rutas, metodo, nombre_sticker=None):
    """
    Procesa una lista completa de videos en secuencia.

    Igual que procesar_lote_imagenes() en procesador_imagen.py,
    asume que la verificación de existencia ya fue hecha por main.py.
    Solo recibe los videos que SÍ deben procesarse.

    Parámetros:
        lista_rutas    (list of str): Rutas de videos a procesar.
        metodo         (str): "blur", "pixelado" o "sticker".
        nombre_sticker (str, opcional): PNG en /recursos.

    Retorna:
        dict con contadores:
            {
                "procesados": int,
                "errores":    int
            }

    NOTA EDUCATIVA — Escalabilidad:
        Este lote es secuencial: procesa un video a la vez.
        Para videos muy largos o muchos archivos, una mejora
        sería usar concurrent.futures.ProcessPoolExecutor para
        distribuir el trabajo en múltiples núcleos del CPU.
        Sin embargo, eso agrega complejidad; esta versión
        prioriza claridad sobre velocidad.

    Ejemplo de uso:
        contadores = procesar_lote_videos(
            ["entradas/video1.mp4", "entradas/video2.avi"],
            "blur"
        )
    """
    contadores = {"procesados": 0, "errores": 0}

    for ruta in lista_rutas:
        exito = procesar_video(ruta, metodo, nombre_sticker)
        if exito:
            contadores["procesados"] += 1
        else:
            contadores["errores"] += 1

    return contadores


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA PARA PRUEBAS INDIVIDUALES
#  Ejecuta: python src/procesador_video.py <video> <metodo>
#  Ejemplo: python src/procesador_video.py entradas/clip.mp4 blur
# ─────────────────────────────────────────────

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("Uso:     python src/procesador_video.py <video> <metodo> [sticker.png]")
        print("Métodos: blur | pixelado | sticker")
        print("Ejemplo: python src/procesador_video.py entradas/clip.mp4 pixelado")
        sys.exit(1)

    ruta_v  = sys.argv[1]
    met     = sys.argv[2]
    sticker = sys.argv[3] if len(sys.argv) > 3 else None

    exito = procesar_video(ruta_v, met, sticker)
    sys.exit(0 if exito else 1)
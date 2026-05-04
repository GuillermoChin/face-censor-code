# ============================================================
#  face-censor-code | Módulo: detector.py
#  Autor: Guillermo Chin — "el chico de las estrellas"
#  Institución: ITESCAM | Campeche, México
#  GitHub: https://github.com/GuillermoChin/face-censor-code
#  Licencia: MIT — Libre uso con atribución
# ------------------------------------------------------------
#  DESCRIPCIÓN:
#  Módulo de detección facial actualizado para MediaPipe 0.10+
#
#  CAMBIO IMPORTANTE respecto a versiones anteriores:
#  MediaPipe 0.10+ eliminó la API "mp.solutions" y migró a
#  la nueva "MediaPipe Tasks API". Este módulo usa la nueva API.
#
#  La nueva API requiere un archivo de modelo .tflite que se
#  descarga automáticamente la primera vez que se ejecuta.
#  Modelo: blaze_face_short_range.tflite (~400 KB)
#  Fuente: Google MediaPipe Model Repository
#
#  CONCEPTOS CLAVE para estudiantes:
#  - TFLite: formato compacto de modelos TensorFlow optimizado
#    para dispositivos con recursos limitados (móviles, edge).
#  - Tasks API: nueva arquitectura de MediaPipe que separa
#    claramente la configuración del modelo de su ejecución.
#  - mp.Image: contenedor de imagen propio de MediaPipe 0.10+
#    que reemplaza el paso directo de numpy arrays.
# ============================================================

import cv2
import numpy as np
import os
import urllib.request
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import DETECCION_CONFIANZA_MINIMA, MARGEN_CARA

# ── Importar la nueva Tasks API de MediaPipe 0.10+ ────────────
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision


# ─────────────────────────────────────────────
#  CONFIGURACIÓN DEL MODELO
# ─────────────────────────────────────────────

# Nombre y ruta local donde se guarda el modelo descargado
NOMBRE_MODELO   = "blaze_face_short_range.tflite"
RUTA_MODELO     = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    NOMBRE_MODELO
)

# URL oficial del modelo en el repositorio de Google MediaPipe
URL_MODELO = (
    "https://storage.googleapis.com/mediapipe-models/"
    "face_detector/blaze_face_short_range/float16/1/"
    "blaze_face_short_range.tflite"
)


# ─────────────────────────────────────────────
#  DESCARGA AUTOMÁTICA DEL MODELO
# ─────────────────────────────────────────────

def descargar_modelo():
    """
    Descarga el modelo TFLite de detección facial si no existe
    en el directorio raíz del proyecto.

    El modelo solo se descarga UNA VEZ (~400 KB).
    En ejecuciones posteriores se reutiliza el archivo local.

    NOTA EDUCATIVA — Modelos preentrenados:
        Los detectores modernos como MediaPipe no calculan
        reglas a mano: usan redes neuronales entrenadas con
        millones de imágenes. El archivo .tflite contiene
        los pesos de esa red ya entrenada, lista para usarse
        sin necesidad de entrenamiento propio.
    """
    if os.path.exists(RUTA_MODELO):
        return  # Ya existe, no es necesario descargar

    print(f"📥  Descargando modelo de detección facial...")
    print(f"    Fuente : {URL_MODELO}")
    print(f"    Destino: {RUTA_MODELO}")
    print(f"    Tamaño : ~400 KB — solo se descarga una vez\n")

    try:
        urllib.request.urlretrieve(URL_MODELO, RUTA_MODELO)
        print(f"✅  Modelo descargado correctamente.\n")
    except Exception as e:
        print(f"❌  Error al descargar el modelo: {e}")
        print("    Descárgalo manualmente desde:")
        print(f"    {URL_MODELO}")
        print(f"    y colócalo en la raíz del proyecto como: {NOMBRE_MODELO}")
        sys.exit(1)


# ─────────────────────────────────────────────
#  INICIALIZACIÓN DEL DETECTOR
# ─────────────────────────────────────────────

def crear_detector(modo_video=True):
    """
    Crea y retorna una instancia del detector facial
    usando la nueva MediaPipe Tasks API (0.10+).

    Descarga el modelo automáticamente si no existe.

    Parámetros:
        modo_video (bool):
            True  → VIDEO mode: optimizado para secuencias de
                    frames, el detector mantiene estado entre
                    llamadas para un tracking más estable.
            False → IMAGE mode: cada imagen se analiza de forma
                    independiente, sin estado previo.

    Retorna:
        mediapipe.tasks.python.vision.FaceDetector:
            Detector listo para usar con detect() o
            detect_for_video().

    NOTA EDUCATIVA — RunningMode:
        La nueva Tasks API distingue explícitamente entre
        tres modos de ejecución:
            IMAGE      → imágenes independientes
            VIDEO      → secuencias con timestamps
            LIVE_STREAM → cámara en tiempo real (async)
        Elegir el modo correcto mejora rendimiento y precisión.

    Ejemplo de uso:
        with crear_detector(modo_video=False) as detector:
            caras = detectar_caras(imagen, detector)
    """
    descargar_modelo()

    # Seleccionar el modo de ejecución según el tipo de entrada
    if modo_video:
        modo = mp_vision.RunningMode.VIDEO
    else:
        modo = mp_vision.RunningMode.IMAGE

    # Configurar opciones del detector
    opciones = mp_vision.FaceDetectorOptions(
        base_options=mp_python.BaseOptions(
            model_asset_path=RUTA_MODELO
        ),
        running_mode=modo,
        min_detection_confidence=DETECCION_CONFIANZA_MINIMA
    )

    return mp_vision.FaceDetector.create_from_options(opciones)


# ─────────────────────────────────────────────
#  DETECCIÓN DE CARAS EN UN FRAME/IMAGEN
# ─────────────────────────────────────────────

def detectar_caras(frame, detector, numero_frame=0, fps=30):
    """
    Detecta todas las caras presentes en un frame o imagen
    y devuelve sus coordenadas en píxeles.

    DIFERENCIA con MediaPipe 0.9:
        La nueva API requiere convertir el frame numpy a un
        objeto mp.Image antes de procesarlo.
        En modo VIDEO requiere además un timestamp en milisegundos
        calculado a partir del número de frame y los FPS.

    Parámetros:
        frame        (numpy.ndarray): Imagen en formato BGR.
        detector     : Instancia activa del detector.
        numero_frame (int): Número del frame actual (para video).
                     En imágenes usa el valor por defecto 0.
        fps          (float): FPS del video (para calcular timestamp).
                     En imágenes usa el valor por defecto 30.

    Retorna:
        list of tuples: Lista de (x, y, ancho, alto) en píxeles.
        Lista vacía si no se detecta ninguna cara.

    NOTA EDUCATIVA — Timestamps en video:
        En modo VIDEO, MediaPipe necesita saber en qué momento
        del tiempo está cada frame para hacer tracking correcto.
        El timestamp se calcula como:
            timestamp_ms = (numero_frame / fps) * 1000
        Ejemplo: frame 30 a 30fps → timestamp = 1000ms (segundo 1)

    Ejemplo de uso:
        # Para imagen:
        caras = detectar_caras(frame, detector)

        # Para video (dentro del loop de frames):
        caras = detectar_caras(frame, detector, numero_frame, fps)
    """
    alto, ancho = frame.shape[:2]

    # ── Paso 1: Convertir BGR (OpenCV) → RGB (MediaPipe) ──────────
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # ── Paso 2: Envolver en mp.Image (nuevo en Tasks API) ─────────
    # La nueva API ya no acepta numpy arrays directamente
    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=frame_rgb
    )

    # ── Paso 3: Ejecutar detección según el modo ──────────────────
    try:
        if detector.running_mode == mp_vision.RunningMode.VIDEO:
            # Modo video: requiere timestamp en milisegundos
            timestamp_ms = int((numero_frame / fps) * 1000)
            resultado = detector.detect_for_video(mp_image, timestamp_ms)
        else:
            # Modo imagen: sin timestamp
            resultado = detector.detect(mp_image)
    except Exception as e:
        print(f"⚠️  Error en detección: {e}")
        return []

    # Sin detecciones, retornar lista vacía
    if not resultado.detections:
        return []

    caras = []

    # ── Paso 4: Convertir bounding boxes normalizadas a píxeles ───
    for deteccion in resultado.detections:

        bbox = deteccion.bounding_box

        # En la nueva API las coordenadas YA vienen en píxeles,
        # no normalizadas como en la versión 0.9
        x = bbox.origin_x
        y = bbox.origin_y
        w = bbox.width
        h = bbox.height

        # ── Paso 5: Aplicar margen extra ──────────────────────────
        x = max(0, x - MARGEN_CARA)
        y = max(0, y - MARGEN_CARA)
        w = min(ancho - x, w + MARGEN_CARA * 2)
        h = min(alto  - y, h + MARGEN_CARA * 2)

        caras.append((x, y, w, h))

    return caras


# ─────────────────────────────────────────────
#  FUNCIÓN DE PRUEBA RÁPIDA (uso educativo)
# ─────────────────────────────────────────────

def probar_detector(ruta_imagen):
    """
    Prueba el detector con una imagen y muestra el resultado
    visualmente con rectángulos verdes sobre las caras.

    Uso:
        $ python src/detector.py entradas/foto.jpg
    """
    imagen = cv2.imread(ruta_imagen)
    if imagen is None:
        print(f"⛔  No se pudo cargar: {ruta_imagen}")
        return

    with crear_detector(modo_video=False) as detector:
        caras = detectar_caras(imagen, detector)

    print(f"🔍  Caras detectadas: {len(caras)}")

    for (x, y, w, h) in caras:
        cv2.rectangle(imagen, (x, y), (x + w, y + h), (0, 255, 0), 2)

    cv2.imshow("Prueba de detección — presiona cualquier tecla para cerrar", imagen)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA PARA PRUEBAS
# ─────────────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) > 1:
        probar_detector(sys.argv[1])
    else:
        print("Uso: python src/detector.py <ruta_imagen>")
        print("Ejemplo: python src/detector.py entradas/foto.jpg")


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA PARA PRUEBAS
#  Solo se ejecuta si corres este archivo directamente:
#  $ python src/detector.py
#  No se ejecuta cuando es importado por otros módulos.
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        probar_detector(sys.argv[1])
    else:
        print("Uso: python src/detector.py <ruta_imagen>")
        print("Ejemplo: python src/detector.py entradas/foto.jpg")
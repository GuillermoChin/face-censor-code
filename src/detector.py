# ============================================================
#  face-censor-code | Módulo: detector.py
#  Autor: Guillermo Chin — "el chico de las estrellas"
#  Institución: ITESCAM | Campeche, México
#  GitHub: https://github.com/GuillermoChin/face-censor-code
#  Licencia: MIT — Libre uso con atribución
# ------------------------------------------------------------
#  DESCRIPCIÓN:
#  Módulo de detección facial usando MediaPipe Face Detection.
#
#  MediaPipe es una biblioteca de Google que provee modelos
#  de visión computacional preentrenados y optimizados.
#  El modelo de detección facial devuelve una "bounding box"
#  (caja delimitadora) por cada cara encontrada en la imagen.
#
#  CONCEPTOS CLAVE para estudiantes:
#  - Bounding box: rectángulo que encierra un objeto detectado.
#    Se representa como (x, y, ancho, alto) en píxeles.
#  - Confianza (confidence): valor entre 0 y 1 que indica
#    qué tan seguro está el modelo de su detección.
#  - Frame: un fotograma individual de un video.
#    Un video de 30fps tiene 30 frames por segundo.
#
#  Referencia oficial MediaPipe:
#  https://developers.google.com/mediapipe/solutions/vision/face_detector
# ============================================================

import cv2
import mediapipe as mp
from config import DETECCION_CONFIANZA_MINIMA, MARGEN_CARA


# ─────────────────────────────────────────────
#  INICIALIZACIÓN DEL DETECTOR
# ─────────────────────────────────────────────

# MediaPipe organiza sus herramientas dentro del objeto "solutions"
# Aquí accedemos al módulo de detección facial
mp_face_detection = mp.solutions.face_detection


def crear_detector(modo_video=True):
    """
    Crea y retorna una instancia del detector facial de MediaPipe.

    Parámetros:
        modo_video (bool):
            True  → optimizado para secuencias de video (reutiliza
                    detecciones entre frames, más rápido).
            False → optimizado para imágenes individuales (más preciso
                    pero más lento, no hay contexto entre frames).

    Retorna:
        mediapipe.solutions.face_detection.FaceDetection:
            Objeto detector listo para usar.

    NOTA EDUCATIVA:
        Esta función separa la CREACIÓN del detector de su USO.
        Esto sigue el principio de responsabilidad única (SRP) del
        diseño de software: cada función hace una sola cosa.

    Ejemplo de uso:
        detector = crear_detector(modo_video=False)  # para imágenes
        detector = crear_detector(modo_video=True)   # para videos
    """
    return mp_face_detection.FaceDetection(
        model_selection=1,                          # 1 = modelo de largo alcance (hasta ~5m)
                                                    # 0 = modelo corto alcance (selfies, hasta ~2m)
        min_detection_confidence=DETECCION_CONFIANZA_MINIMA
    )


# ─────────────────────────────────────────────
#  DETECCIÓN DE CARAS EN UN FRAME/IMAGEN
# ─────────────────────────────────────────────

def detectar_caras(frame, detector):
    """
    Detecta todas las caras presentes en un frame o imagen
    y devuelve sus coordenadas en píxeles.

    FLUJO INTERNO:
        1. OpenCV trabaja en BGR, MediaPipe necesita RGB
           → convertimos el frame antes de procesarlo
        2. MediaPipe analiza la imagen y devuelve detecciones
           cada detección tiene una "bounding box" normalizada
           (valores entre 0.0 y 1.0, relativos al tamaño)
        3. Multiplicamos por el tamaño real para obtener píxeles
        4. Aplicamos un margen extra (MARGEN_CARA) para cubrir
           bien toda la cabeza

    Parámetros:
        frame   (numpy.ndarray): Imagen en formato BGR (como la
                                 entrega OpenCV al leer un archivo).
        detector: Instancia activa del detector (de crear_detector()).

    Retorna:
        list of tuples: Lista de coordenadas de caras detectadas.
            Cada elemento es una tupla: (x, y, ancho, alto)
            donde (x, y) es la esquina superior izquierda.
            Lista vacía si no se detecta ninguna cara.

    NOTA EDUCATIVA — Coordenadas normalizadas vs píxeles:
        MediaPipe no retorna "la cara está en el píxel 320".
        Retorna "la cara está al 40% del ancho de la imagen".
        Esto permite que el modelo funcione con cualquier resolución.
        Nosotros lo convertimos a píxeles multiplicando:
            x_pixeles = x_normalizado * ancho_imagen

    Ejemplo de uso:
        caras = detectar_caras(frame, detector)
        for (x, y, w, h) in caras:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)
    """
    # Obtenemos dimensiones reales del frame
    alto, ancho, _ = frame.shape

    # ── Paso 1: Convertir BGR (OpenCV) → RGB (MediaPipe) ──────────
    # OpenCV carga imágenes en orden Azul-Verde-Rojo (BGR)
    # MediaPipe espera Rojo-Verde-Azul (RGB)
    # cv2.cvtColor hace esa conversión de canal
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # ── Paso 2: Ejecutar la detección ─────────────────────────────
    # El objeto "resultados" contiene una lista de detecciones,
    # cada una con su bounding box y puntos clave del rostro
    resultados = detector.process(frame_rgb)

    # Si no hay caras detectadas, retornar lista vacía
    if not resultados.detections:
        return []

    caras = []

    # ── Paso 3: Convertir bounding boxes a coordenadas en píxeles ──
    for deteccion in resultados.detections:

        # bboxC = bounding box relativa (Coordinates normalizadas)
        bboxC = deteccion.location_data.relative_bounding_box

        # Convertir de normalizado (0-1) a píxeles reales
        x = int(bboxC.xmin * ancho)
        y = int(bboxC.ymin * alto)
        w = int(bboxC.width  * ancho)
        h = int(bboxC.height * alto)

        # ── Paso 4: Aplicar margen extra ──────────────────────────
        # Expandimos la caja para cubrir mejor frente, cabello y mentón
        x = max(0, x - MARGEN_CARA)          # no salir del borde izquierdo
        y = max(0, y - MARGEN_CARA)          # no salir del borde superior
        w = min(ancho - x, w + MARGEN_CARA * 2)
        h = min(alto  - y, h + MARGEN_CARA * 2)

        caras.append((x, y, w, h))

    return caras


# ─────────────────────────────────────────────
#  FUNCIÓN DE PRUEBA RÁPIDA (uso educativo)
# ─────────────────────────────────────────────

def probar_detector(ruta_imagen):
    """
    Función auxiliar para probar el detector con una sola imagen
    y visualizar el resultado directamente en pantalla.

    Dibuja un rectángulo verde sobre cada cara detectada
    y muestra la imagen en una ventana emergente.

    Parámetros:
        ruta_imagen (str): Ruta a cualquier imagen de prueba.

    USO:
        Ejecuta este archivo directamente para probarlo:
        $ python src/detector.py

    NOTA: Esta función NO se usa en el pipeline principal.
          Es solo para pruebas y demostración en clase.
    """
    # Cargar imagen con OpenCV
    imagen = cv2.imread(ruta_imagen)
    if imagen is None:
        print(f"⛔  No se pudo cargar la imagen: {ruta_imagen}")
        return

    # Crear detector en modo imagen (no video)
    with crear_detector(modo_video=False) as detector:
        caras = detectar_caras(imagen, detector)

    print(f"🔍  Caras detectadas: {len(caras)}")

    # Dibujar rectángulos verdes sobre cada cara
    for (x, y, w, h) in caras:
        cv2.rectangle(imagen, (x, y), (x + w, y + h), (0, 255, 0), 2)

    # Mostrar imagen resultante
    cv2.imshow("Prueba de detección", imagen)
    cv2.waitKey(0)       # Esperar a que el usuario presione cualquier tecla
    cv2.destroyAllWindows()


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
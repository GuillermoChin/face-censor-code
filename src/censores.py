# ============================================================
#  face-censor-code | Módulo: censores.py
#  Autor: Guillermo Chin — "el chico de las estrellas"
#  Institución: ITESCAM | Campeche, México
#  GitHub: https://github.com/GuillermoChin/face-censor-code
#  Licencia: MIT — Libre uso con atribución
# ------------------------------------------------------------
#  DESCRIPCIÓN:
#  Módulo de métodos de censura facial.
#  Contiene tres funciones independientes, cada una aplica
#  un tipo diferente de censura sobre una región de la imagen:
#
#    1. aplicar_blur()    → Desenfoque gaussiano
#    2. aplicar_pixel()   → Efecto mosaico/pixelado
#    3. aplicar_sticker() → Superponer imagen PNG con transparencia
#
#  Todas reciben un frame (imagen numpy) y una lista de caras
#  en formato [(x, y, w, h), ...] y retornan el frame modificado.
#
#  CONCEPTOS CLAVE para estudiantes:
#  - numpy.ndarray: estructura de datos que representa una imagen
#    como una matriz de píxeles. Cada píxel tiene 3 valores (BGR).
#  - ROI (Region of Interest): submatriz que recorta solo la zona
#    de la cara dentro del frame completo.
#  - Canal alfa: cuarto canal de una imagen PNG que representa
#    la transparencia (0 = invisible, 255 = opaco).
#  - Gaussian Blur: filtro que promedia píxeles vecinos con un
#    peso gaussiano, produciendo un efecto de desenfoque suave.
# ============================================================

import cv2
import numpy as np
import os
from config import (
    BLUR_INTENSIDAD,
    PIXEL_BLOQUE,
    STICKER_DEFECTO,
    RUTA_RECURSOS,
)


# ─────────────────────────────────────────────
#  MÉTODO 1: DESENFOQUE GAUSSIANO (BLUR)
# ─────────────────────────────────────────────

def aplicar_blur(frame, caras):
    """
    Aplica desenfoque gaussiano sobre cada cara detectada.

    El desenfoque gaussiano funciona reemplazando cada píxel
    por un promedio ponderado de sus vecinos. Con un kernel
    grande (ej. 99x99), el resultado es una zona completamente
    irreconocible pero de aspecto suave y natural.

    FLUJO:
        1. Para cada cara (x, y, w, h):
        2. Recortar la ROI (región de la cara) del frame
        3. Aplicar cv2.GaussianBlur sobre esa ROI
        4. Pegar la ROI difuminada de vuelta en el frame

    Parámetros:
        frame (numpy.ndarray): Imagen completa en formato BGR.
        caras (list of tuples): Lista de (x, y, w, h) en píxeles.

    Retorna:
        numpy.ndarray: Frame con las caras desenfocadas.

    NOTA EDUCATIVA — ¿Por qué el kernel debe ser impar?
        cv2.GaussianBlur requiere un tamaño de kernel impar
        (51, 71, 99...) para que exista un píxel central
        alrededor del cual se calcula el promedio.
        Un kernel par no tiene centro definido y causa error.

    Ejemplo de uso:
        frame_censurado = aplicar_blur(frame, caras)
    """
    # Hacemos una copia para no modificar el frame original
    resultado = frame.copy()

    for (x, y, w, h) in caras:

        # ── Recortar la ROI de la cara ─────────────────────────
        # En numpy, los arreglos se indexan como [filas, columnas]
        # Las filas corresponden al eje Y, las columnas al eje X
        roi = resultado[y:y+h, x:x+w]

        # ── Aplicar el desenfoque gaussiano ────────────────────
        # El tercer argumento (0) le dice a OpenCV que calcule
        # automáticamente la desviación estándar del kernel
        roi_blur = cv2.GaussianBlur(
            roi,
            (BLUR_INTENSIDAD, BLUR_INTENSIDAD),  # tamaño del kernel (debe ser impar)
            0
        )

        # ── Reemplazar la ROI original con la difuminada ───────
        resultado[y:y+h, x:x+w] = roi_blur

    return resultado


# ─────────────────────────────────────────────
#  MÉTODO 2: PIXELADO (EFECTO MOSAICO)
# ─────────────────────────────────────────────

def aplicar_pixel(frame, caras):
    """
    Aplica efecto de mosaico (pixelado) sobre cada cara detectada.

    El efecto se logra reduciendo la ROI a un tamaño muy pequeño
    y luego escalándola de vuelta a su tamaño original.
    Al agrandar una imagen pequeña, cada "mini-píxel" se convierte
    en un bloque de color sólido, creando el efecto de mosaico.

    FLUJO:
        1. Para cada cara (x, y, w, h):
        2. Recortar la ROI
        3. Reducir la ROI a (w//bloque, h//bloque) — muy pequeña
        4. Escalar de vuelta al tamaño original con interpolación NEAREST
           (NEAREST conserva los bloques sólidos, no suaviza)
        5. Pegar de vuelta en el frame

    Parámetros:
        frame (numpy.ndarray): Imagen completa en formato BGR.
        caras (list of tuples): Lista de (x, y, w, h) en píxeles.

    Retorna:
        numpy.ndarray: Frame con las caras pixeladas.

    NOTA EDUCATIVA — Interpolación NEAREST vs LINEAR:
        Cuando escalamos una imagen, OpenCV necesita "inventar"
        píxeles nuevos. Con INTER_LINEAR suaviza los bordes.
        Con INTER_NEAREST copia el píxel más cercano sin mezclar,
        lo que conserva los bloques duros del efecto mosaico.

    Ejemplo de uso:
        frame_censurado = aplicar_pixel(frame, caras)
    """
    resultado = frame.copy()

    for (x, y, w, h) in caras:

        roi = resultado[y:y+h, x:x+w]

        # ── Calcular tamaño reducido ───────────────────────────
        # Dividimos entre el tamaño del bloque.
        # Ej: una cara de 200x200 con bloque=20 → se reduce a 10x10
        pequeño_w = max(1, w // PIXEL_BLOQUE)   # max(1,...) evita división a 0
        pequeño_h = max(1, h // PIXEL_BLOQUE)

        # ── Reducir la ROI ────────────────────────────────────
        roi_pequeña = cv2.resize(
            roi,
            (pequeño_w, pequeño_h),
            interpolation=cv2.INTER_LINEAR   # suavizado al reducir
        )

        # ── Escalar de vuelta al tamaño original ──────────────
        # INTER_NEAREST preserva los bloques sólidos (efecto mosaico)
        roi_pixelada = cv2.resize(
            roi_pequeña,
            (w, h),
            interpolation=cv2.INTER_NEAREST
        )

        resultado[y:y+h, x:x+w] = roi_pixelada

    return resultado


# ─────────────────────────────────────────────
#  MÉTODO 3: STICKER / OVERLAY PNG
# ─────────────────────────────────────────────

def aplicar_sticker(frame, caras, nombre_sticker=None):
    """
    Superpone una imagen PNG (con transparencia) sobre cada cara.

    Los archivos PNG pueden tener un canal alfa que define la
    transparencia de cada píxel. Esta función usa ese canal para
    mezclar el sticker sobre el frame sin dejar un rectángulo sólido.

    FLUJO:
        1. Cargar el PNG desde /recursos (con canal alfa)
        2. Para cada cara (x, y, w, h):
            a. Redimensionar el sticker al tamaño de la cara
            b. Separar canales BGR y canal alfa del sticker
            c. Crear máscara de transparencia normalizada (0.0 a 1.0)
            d. Mezclar píxel a píxel: sticker * alfa + frame * (1 - alfa)
            e. Pegar el resultado en el frame

    Parámetros:
        frame           (numpy.ndarray): Imagen completa en BGR.
        caras           (list of tuples): Lista de (x, y, w, h).
        nombre_sticker  (str, opcional): Nombre del archivo PNG en
                        /recursos. Si es None, usa STICKER_DEFECTO.

    Retorna:
        numpy.ndarray: Frame con stickers superpuestos.
        Si el sticker no se encuentra, aplica blur como respaldo.

    NOTA EDUCATIVA — Composición alfa (alpha compositing):
        La fórmula de mezcla es:
            pixel_final = pixel_sticker * alfa + pixel_frame * (1 - alfa)
        Cuando alfa=1.0 el sticker es completamente opaco.
        Cuando alfa=0.0 se ve solo el frame original.
        Valores intermedios producen transparencia parcial.
        Este es el mismo principio que usan Photoshop y After Effects.

    Ejemplo de uso:
        frame_censurado = aplicar_sticker(frame, caras, "emoji_star.png")
    """
    resultado = frame.copy()

    # ── Determinar qué sticker usar ───────────────────────────────
    if nombre_sticker is None:
        nombre_sticker = STICKER_DEFECTO

    ruta_sticker = os.path.join(RUTA_RECURSOS, nombre_sticker)

    # ── Cargar el PNG con canal alfa (IMREAD_UNCHANGED) ───────────
    # IMREAD_UNCHANGED es crucial: carga los 4 canales (BGRA).
    # Sin este flag, OpenCV descarta el canal de transparencia.
    sticker_original = cv2.imread(ruta_sticker, cv2.IMREAD_UNCHANGED)

    if sticker_original is None:
        print(f"⚠️  Sticker no encontrado: {ruta_sticker}")
        print("   Se aplicará blur como método alternativo.")
        return aplicar_blur(resultado, caras)   # respaldo automático

    # Verificar que el PNG tiene canal alfa (4 canales: BGRA)
    tiene_alfa = sticker_original.shape[2] == 4

    for (x, y, w, h) in caras:

        # ── Redimensionar sticker al tamaño exacto de la cara ─────
        sticker = cv2.resize(sticker_original, (w, h))

        if tiene_alfa:
            # ── Separar BGR y canal alfa ───────────────────────────
            sticker_bgr  = sticker[:, :, :3]     # primeros 3 canales: color
            sticker_alfa = sticker[:, :, 3]      # cuarto canal: transparencia

            # ── Normalizar alfa de 0-255 a 0.0-1.0 ────────────────
            # np.newaxis agrega una dimensión para que la multiplicación
            # funcione correctamente con los 3 canales de color
            alfa = sticker_alfa.astype(np.float32) / 255.0
            alfa = alfa[:, :, np.newaxis]         # shape: (h, w, 1)

            # ── Recortar la ROI del frame ──────────────────────────
            roi = resultado[y:y+h, x:x+w].astype(np.float32)
            sticker_float = sticker_bgr.astype(np.float32)

            # ── Composición alfa: mezcla píxel a píxel ────────────
            # Fórmula: resultado = sticker * alfa + fondo * (1 - alfa)
            mezclado = sticker_float * alfa + roi * (1.0 - alfa)

            # ── Convertir de vuelta a uint8 y pegar en el frame ───
            resultado[y:y+h, x:x+w] = mezclado.astype(np.uint8)

        else:
            # Si el PNG no tiene transparencia, pegarlo directo
            resultado[y:y+h, x:x+w] = sticker[:, :, :3]

    return resultado


# ─────────────────────────────────────────────
#  FUNCIÓN DESPACHADORA
#  Permite elegir el método por nombre (string)
#  en lugar de llamar cada función por separado.
# ─────────────────────────────────────────────

def aplicar_censura(frame, caras, metodo, nombre_sticker=None):
    """
    Función central que despacha al método de censura correcto
    según el nombre recibido como string.

    Esto permite que procesador_video.py y procesador_imagen.py
    llamen a UN SOLO punto de entrada sin importar el método elegido,
    siguiendo el patrón de diseño "Strategy" (estrategia intercambiable).

    Parámetros:
        frame          (numpy.ndarray): Frame o imagen a procesar.
        caras          (list of tuples): Lista de (x, y, w, h).
        metodo         (str): "blur", "pixelado" o "sticker".
        nombre_sticker (str, opcional): Solo necesario si metodo="sticker".

    Retorna:
        numpy.ndarray: Frame con censura aplicada.

    Lanza:
        ValueError si el método no es válido.

    Ejemplo de uso:
        frame_ok = aplicar_censura(frame, caras, "pixelado")
        frame_ok = aplicar_censura(frame, caras, "sticker", "emoji.png")
    """
    from config import METODO_BLUR, METODO_PIXEL, METODO_STICKER

    if metodo == METODO_BLUR:
        return aplicar_blur(frame, caras)

    elif metodo == METODO_PIXEL:
        return aplicar_pixel(frame, caras)

    elif metodo == METODO_STICKER:
        return aplicar_sticker(frame, caras, nombre_sticker)

    else:
        raise ValueError(
            f"⛔  Método de censura no reconocido: '{metodo}'\n"
            f"    Opciones válidas: blur | pixelado | sticker"
        )


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA PARA PRUEBAS
#  Ejecuta: python src/censores.py <imagen> <metodo>
#  Ejemplo: python src/censores.py entradas/foto.jpg blur
# ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

    from detector import crear_detector, detectar_caras

    if len(sys.argv) < 3:
        print("Uso:     python src/censores.py <imagen> <metodo> [sticker.png]")
        print("Métodos: blur | pixelado | sticker")
        print("Ejemplo: python src/censores.py entradas/foto.jpg pixelado")
        sys.exit(1)

    ruta  = sys.argv[1]
    met   = sys.argv[2]
    stick = sys.argv[3] if len(sys.argv) > 3 else None

    imagen = cv2.imread(ruta)
    if imagen is None:
        print(f"⛔  No se pudo cargar: {ruta}")
        sys.exit(1)

    with crear_detector(modo_video=False) as det:
        caras = detectar_caras(imagen, det)

    print(f"🔍  Caras detectadas: {len(caras)}")

    if caras:
        resultado = aplicar_censura(imagen, caras, met, stick)
        cv2.imshow(f"Censura: {met}", resultado)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("ℹ️  No se encontraron caras en la imagen.")
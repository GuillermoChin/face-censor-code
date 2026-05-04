# ============================================================
#  face-censor-code | Módulo: procesador_imagen.py
#  Autor: Guillermo Chin — "el chico de las estrellas"
#  Institución: ITESCAM | Campeche, México
#  GitHub: https://github.com/GuillermoChin/face-censor-code
#  Licencia: MIT — Libre uso con atribución
# ------------------------------------------------------------
#  DESCRIPCIÓN:
#  Módulo encargado del pipeline completo de procesamiento
#  para archivos de imagen.
#
#  Su responsabilidad es:
#    1. Recibir la ruta de una imagen de entrada
#    2. Cargarla con OpenCV
#    3. Detectar caras con detector.py
#    4. Aplicar el método de censura con censores.py
#    5. Guardar el resultado en /salida
#
#  Este módulo NO decide si el archivo ya existe (eso lo hace
#  utils.py antes de llamar aquí) ni elige el método de censura
#  (eso lo decide el usuario en main.py).
#  Aquí solo se ejecuta el pipeline de transformación.
#
#  CONCEPTOS CLAVE para estudiantes:
#  - Pipeline: secuencia de pasos donde la salida de uno
#    es la entrada del siguiente. Es un patrón muy común
#    en procesamiento de señales e imágenes.
#  - cv2.imread(): carga una imagen del disco como numpy array.
#  - cv2.imwrite(): guarda un numpy array como archivo de imagen.
#  - Context manager (with): garantiza que el detector se cierre
#    correctamente al terminar, liberando memoria del modelo.
# ============================================================

import cv2
import os
import sys

# Asegurar que Python encuentre los módulos del proyecto
# cuando este archivo se ejecuta directamente desde /src
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from detector import crear_detector, detectar_caras
from censores import aplicar_censura
from config import (
    DETECCION_MODO_VIDEO,
    MSG_PROCESANDO,
    MSG_LISTO,
    MSG_NO_CARA,
)
from utils import construir_ruta_salida


# ─────────────────────────────────────────────
#  PIPELINE PRINCIPAL DE IMAGEN
# ─────────────────────────────────────────────

def procesar_imagen(ruta_entrada, metodo, nombre_sticker=None):
    """
    Ejecuta el pipeline completo de censura sobre una imagen.

    Pasos internos:
        1. Mostrar mensaje de inicio
        2. Cargar imagen desde disco con OpenCV
        3. Crear detector MediaPipe en modo imagen
        4. Detectar coordenadas de caras
        5. Si hay caras → aplicar censura
        6. Si no hay caras → guardar imagen sin modificar
        7. Guardar resultado en /salida con el mismo nombre

    Parámetros:
        ruta_entrada   (str): Ruta completa al archivo en /entradas.
        metodo         (str): "blur", "pixelado" o "sticker".
        nombre_sticker (str, opcional): Nombre del PNG en /recursos.
                       Solo necesario cuando metodo="sticker".

    Retorna:
        bool:
            True  → imagen procesada y guardada correctamente.
            False → ocurrió un error (imagen no cargada, escritura
                    fallida, etc.).

    NOTA EDUCATIVA — ¿Por qué retornar bool y no lanzar excepción?
        En pipelines por lotes (batch processing) donde se procesan
        muchos archivos, es preferible manejar errores por archivo
        de forma silenciosa y continuar con el siguiente, en lugar
        de detener todo el proceso con una excepción.
        El bool permite que main.py lleve un conteo de errores.

    Ejemplo de uso:
        exito = procesar_imagen("entradas/foto.jpg", "blur")
        exito = procesar_imagen("entradas/retrato.png", "sticker", "emoji.png")
    """
    nombre = os.path.basename(ruta_entrada)
    print(MSG_PROCESANDO.format(nombre=nombre))

    # ── Paso 1: Cargar la imagen ───────────────────────────────────
    # cv2.imread retorna None si el archivo no existe o está corrupto
    imagen = cv2.imread(ruta_entrada)

    if imagen is None:
        print(f"❌  No se pudo cargar la imagen: {nombre}")
        print("    Verifica que el archivo no esté corrupto o en uso.")
        return False

    # ── Paso 2: Detectar caras ────────────────────────────────────
    # modo_video=False → optimizado para imágenes individuales
    # Usamos "with" para garantizar que MediaPipe libere sus recursos
    # al terminar, incluso si ocurre un error en el proceso
    with crear_detector(modo_video=False) as detector:
        caras = detectar_caras(imagen, detector)

    # ── Paso 3: Aplicar censura o conservar imagen original ────────
    if not caras:
        # No se encontraron caras: guardar imagen sin cambios
        # pero notificar al usuario
        print(MSG_NO_CARA.format(nombre=nombre))
        imagen_resultado = imagen

    else:
        # Se encontraron caras: aplicar el método elegido
        print(f"   👤  Caras detectadas: {len(caras)}")
        imagen_resultado = aplicar_censura(
            imagen,
            caras,
            metodo,
            nombre_sticker
        )

    # ── Paso 4: Guardar el resultado en /salida ────────────────────
    ruta_salida = construir_ruta_salida(ruta_entrada, "imagen")

    # cv2.imwrite retorna True si la escritura fue exitosa
    guardado = cv2.imwrite(ruta_salida, imagen_resultado)

    if not guardado:
        print(f"❌  Error al guardar: {ruta_salida}")
        print("    Verifica que la carpeta /salida exista y tenga permisos.")
        return False

    print(MSG_LISTO.format(nombre=os.path.basename(ruta_salida)))
    return True


# ─────────────────────────────────────────────
#  PROCESAMIENTO POR LOTE DE IMÁGENES
# ─────────────────────────────────────────────

def procesar_lote_imagenes(lista_rutas, metodo, nombre_sticker=None):
    """
    Procesa una lista completa de imágenes en secuencia.

    Itera sobre cada ruta, llama a procesar_imagen() y lleva
    un conteo de cuántas se procesaron correctamente y cuántas
    fallaron.

    Esta función asume que la verificación de existencia en /salida
    ya fue realizada por main.py antes de incluir cada ruta en
    la lista. Solo recibe las que SÍ deben procesarse.

    Parámetros:
        lista_rutas    (list of str): Rutas de imágenes a procesar.
        metodo         (str): "blur", "pixelado" o "sticker".
        nombre_sticker (str, opcional): PNG en /recursos para sticker.

    Retorna:
        dict con contadores:
            {
                "procesados": int,  ← imágenes exitosas
                "errores":    int   ← imágenes fallidas
            }

    NOTA EDUCATIVA — Procesamiento por lotes (Batch Processing):
        Cuando se necesita aplicar la misma operación a muchos
        archivos, se habla de "batch processing". Es un concepto
        fundamental en ciencias de la computación, usado desde
        sistemas operativos hasta pipelines de Machine Learning.
        Aquí iteramos la lista secuencialmente (un archivo a la vez).
        Una mejora futura podría usar multiprocessing para
        procesar varios archivos en paralelo y reducir el tiempo total.

    Ejemplo de uso:
        contadores = procesar_lote_imagenes(
            ["entradas/a.jpg", "entradas/b.png"],
            "pixelado"
        )
        print(contadores["procesados"])  # → 2
    """
    contadores = {"procesados": 0, "errores": 0}

    for ruta in lista_rutas:
        exito = procesar_imagen(ruta, metodo, nombre_sticker)
        if exito:
            contadores["procesados"] += 1
        else:
            contadores["errores"] += 1

    return contadores


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA PARA PRUEBAS INDIVIDUALES
#  Ejecuta: python src/procesador_imagen.py <imagen> <metodo>
#  Ejemplo: python src/procesador_imagen.py entradas/foto.jpg blur
# ─────────────────────────────────────────────

if __name__ == "__main__":

    if len(sys.argv) < 3:
        print("Uso:     python src/procesador_imagen.py <imagen> <metodo> [sticker.png]")
        print("Métodos: blur | pixelado | sticker")
        print("Ejemplo: python src/procesador_imagen.py entradas/foto.jpg pixelado")
        sys.exit(1)

    ruta_img  = sys.argv[1]
    met       = sys.argv[2]
    sticker   = sys.argv[3] if len(sys.argv) > 3 else None

    exito = procesar_imagen(ruta_img, met, sticker)
    sys.exit(0 if exito else 1)
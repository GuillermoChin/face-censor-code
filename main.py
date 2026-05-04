# ============================================================
#  face-censor-code | Módulo: main.py
#  Autor: Guillermo Chin — "el chico de las estrellas"
#  Institución: ITESCAM | Campeche, México
#  GitHub: https://github.com/GuillermoChin/face-censor-code
#  Licencia: MIT — Libre uso con atribución
# ------------------------------------------------------------
#  DESCRIPCIÓN:
#  Punto de entrada principal del sistema face-censor-code.
#
#  Este archivo orquesta todos los módulos del proyecto:
#    1. Verifica que la estructura de carpetas exista
#    2. Muestra el menú interactivo al usuario
#    3. Escanea la carpeta /entradas
#    4. Verifica qué archivos ya fueron procesados
#    5. Lanza el pipeline de imágenes y/o videos
#    6. Muestra el resumen final
#
#  CÓMO EJECUTAR:
#    $ python main.py
#
#  CONCEPTOS CLAVE para estudiantes:
#  - Punto de entrada: en Python, el archivo que se ejecuta
#    directamente se identifica con if __name__ == "__main__".
#    Los módulos importados NO ejecutan ese bloque.
#  - Orquestador: patrón de diseño donde un módulo central
#    coordina el trabajo de otros módulos especializados,
#    sin realizar él mismo el procesamiento pesado.
#  - Separación de responsabilidades (SoC): cada módulo hace
#    una sola cosa. main.py solo coordina; no procesa píxeles.
# ============================================================

import os
import sys

# ── Importar todos los módulos del proyecto ───────────────────
from config import (
    RUTA_ENTRADAS,
    RUTA_SALIDA,
    RUTA_RECURSOS,
    METODOS_VALIDOS,
    METODO_BLUR,
    METODO_PIXEL,
    METODO_STICKER,
    MSG_METODO_INVALIDO,
    verificar_estructura,
)
from utils import (
    escanear_entradas,
    ya_fue_procesado,
    listar_stickers,
    imprimir_separador,
    imprimir_resumen,
)
from procesador_imagen import procesar_lote_imagenes
from procesador_video  import procesar_lote_videos


# ─────────────────────────────────────────────
#  BANNER DE BIENVENIDA
# ─────────────────────────────────────────────

def mostrar_banner():
    """
    Muestra el banner de bienvenida al iniciar el sistema.

    El banner cumple una función educativa importante:
    identifica claramente el proyecto, su autor y su propósito,
    siguiendo buenas prácticas de documentación en software.
    """
    print("""
╔══════════════════════════════════════════════════════╗
║           FACE CENSOR CODE  v1.0                     ║
║   Sistema automático de censura facial               ║
║                                                      ║
║   Autor : Guillermo Chin                             ║
║           "el chico de las estrellas"                ║
║   Inst. : ITESCAM | Campeche, México                 ║
║   GitHub: github.com/GuillermoChin/face-censor-code  ║
║   Lic.  : MIT — Libre uso con atribución             ║
╚══════════════════════════════════════════════════════╝
    """)


# ─────────────────────────────────────────────
#  MENÚ: SELECCIÓN DE MÉTODO DE CENSURA
# ─────────────────────────────────────────────

def menu_metodo():
    """
    Muestra el menú de selección de método de censura
    y valida la entrada del usuario en un bucle hasta
    que elija una opción válida.

    Retorna:
        str: Uno de los métodos válidos definidos en config.py
             ("blur", "pixelado" o "sticker").

    NOTA EDUCATIVA — Validación de entrada:
        Nunca asumas que el usuario escribirá exactamente
        lo que esperas. El bucle while True + break es el
        patrón clásico para validar entradas interactivas.
        .strip() elimina espacios accidentales al inicio/fin.
        .lower() hace la comparación insensible a mayúsculas.
    """
    imprimir_separador("MÉTODO DE CENSURA")
    print()
    print("  [1] blur      → Desenfoque gaussiano (suave y natural)")
    print("  [2] pixelado  → Efecto mosaico (estilo retro)")
    print("  [3] sticker   → Superponer imagen PNG desde /recursos")
    print()

    while True:
        entrada = input("  Elige una opción (1/2/3) o escribe el nombre: ").strip().lower()

        # Aceptar tanto número como nombre del método
        if entrada == "1" or entrada == METODO_BLUR:
            return METODO_BLUR

        elif entrada == "2" or entrada == METODO_PIXEL:
            return METODO_PIXEL

        elif entrada == "3" or entrada == METODO_STICKER:
            return METODO_STICKER

        else:
            print(MSG_METODO_INVALIDO.format(metodos=", ".join(METODOS_VALIDOS)))


# ─────────────────────────────────────────────
#  MENÚ: SELECCIÓN DE STICKER
# ─────────────────────────────────────────────

def menu_sticker():
    """
    Cuando el usuario elige el método "sticker", este menú
    muestra los archivos PNG disponibles en /recursos y
    permite elegir cuál usar.

    Si no hay stickers disponibles, avisa al usuario y
    ofrece continuar con blur como método alternativo.

    Retorna:
        str o None:
            Nombre del archivo PNG elegido, o None si no hay
            stickers y el usuario prefiere usar blur.

    NOTA EDUCATIVA — Manejo de casos vacíos:
        Siempre contempla el caso donde una lista puede estar
        vacía. Un sistema robusto nunca asume que habrá datos;
        siempre verifica y ofrece una alternativa.
    """
    imprimir_separador("SELECCIÓN DE STICKER")

    stickers = listar_stickers(RUTA_RECURSOS)

    if not stickers:
        print(f"\n  ⚠️  No se encontraron archivos PNG en /{RUTA_RECURSOS}")
        print("     Coloca imágenes .png en esa carpeta para usar este método.")
        print()
        respuesta = input("  ¿Deseas continuar con BLUR como alternativa? (s/n): ").strip().lower()
        if respuesta == "s":
            return None   # None activa el fallback a blur en censores.py
        else:
            print("  Operación cancelada.")
            sys.exit(0)

    # Mostrar lista numerada de stickers disponibles
    print("\n  Stickers disponibles en /recursos:\n")
    for i, nombre in enumerate(stickers, start=1):
        print(f"    [{i}] {nombre}")
    print()

    while True:
        entrada = input(f"  Elige un número (1-{len(stickers)}): ").strip()

        # Validar que sea un número dentro del rango
        if entrada.isdigit():
            indice = int(entrada) - 1
            if 0 <= indice < len(stickers):
                elegido = stickers[indice]
                print(f"  ✅  Sticker seleccionado: {elegido}")
                return elegido

        print(f"  ⛔  Opción no válida. Elige entre 1 y {len(stickers)}.")


# ─────────────────────────────────────────────
#  FILTRADO DE ARCHIVOS PENDIENTES
# ─────────────────────────────────────────────

def filtrar_pendientes(archivos, tipo):
    """
    Filtra la lista de archivos de un tipo dado y separa
    los que ya fueron procesados de los que aún no.

    Para cada archivo ya procesado, imprime el mensaje
    de aviso definido en config.py y lo excluye de la lista.

    Parámetros:
        archivos (list of str): Lista de rutas del tipo dado.
        tipo     (str): "imagen" o "video".

    Retorna:
        tuple (list, int):
            - Lista de rutas que AÚN necesitan procesarse.
            - Cantidad de archivos omitidos (ya existían).

    NOTA EDUCATIVA — List comprehension vs bucle for:
        Aquí usamos un bucle for clásico porque necesitamos
        ejecutar un efecto secundario (imprimir aviso) para
        cada archivo omitido. Una list comprehension sería
        más compacta pero no permitiría el print intermedio.

    Ejemplo de uso:
        pendientes, omitidos = filtrar_pendientes(videos, "video")
    """
    pendientes = []
    omitidos   = 0

    for ruta in archivos:
        if ya_fue_procesado(ruta, tipo):
            omitidos += 1
        else:
            pendientes.append(ruta)

    return pendientes, omitidos


# ─────────────────────────────────────────────
#  FUNCIÓN PRINCIPAL
# ─────────────────────────────────────────────

def main():
    """
    Función principal que orquesta todo el sistema.

    Flujo completo:
        1. Mostrar banner
        2. Verificar/crear estructura de carpetas
        3. Escanear /entradas y clasificar archivos
        4. Verificar si hay algo que procesar
        5. Mostrar menú de método de censura
        6. Si aplica, mostrar menú de sticker
        7. Filtrar archivos ya procesados
        8. Procesar imágenes pendientes
        9. Procesar videos pendientes
       10. Mostrar resumen final

    No recibe parámetros ni retorna valores.
    Es el punto de entrada del sistema completo.
    """

    # ── Paso 1: Banner ─────────────────────────────────────────────
    mostrar_banner()

    # ── Paso 2: Verificar estructura de carpetas ───────────────────
    # Si /entradas, /salida o /recursos no existen, los crea
    verificar_estructura()

    # ── Paso 3: Escanear /entradas ─────────────────────────────────
    imprimir_separador("ESCANEANDO ENTRADAS")
    archivos = escanear_entradas()

    total_imagenes    = len(archivos["imagenes"])
    total_videos      = len(archivos["videos"])
    total_desconocidos = len(archivos["desconocidos"])

    print(f"\n  🖼️   Imágenes encontradas  : {total_imagenes}")
    print(f"  🎬  Videos encontrados    : {total_videos}")

    if total_desconocidos > 0:
        print(f"  ⛔  Archivos no soportados: {total_desconocidos}")
        for ruta in archivos["desconocidos"]:
            print(f"       → {os.path.basename(ruta)}")

    # ── Paso 4: Verificar si hay algo que procesar ─────────────────
    if total_imagenes == 0 and total_videos == 0:
        print("\n  ℹ️  No se encontraron archivos para procesar.")
        print(f"     Coloca imágenes o videos en la carpeta /{RUTA_ENTRADAS}")
        sys.exit(0)

    print()

    # ── Paso 5: Menú de método de censura ──────────────────────────
    metodo = menu_metodo()
    print(f"\n  ✅  Método seleccionado: {metodo.upper()}\n")

    # ── Paso 6: Menú de sticker (solo si aplica) ───────────────────
    nombre_sticker = None
    if metodo == METODO_STICKER:
        nombre_sticker = menu_sticker()
        # Si menu_sticker() retorna None, censores.py usará blur
        # como fallback automático (ya está implementado)
        if nombre_sticker is None:
            metodo = METODO_BLUR
            print("  ↩️  Cambiando a método: BLUR\n")

    # ── Paso 7: Filtrar archivos ya procesados ─────────────────────
    imprimir_separador("VERIFICANDO ARCHIVOS EXISTENTES")

    imagenes_pendientes, imagenes_omitidas = filtrar_pendientes(
        archivos["imagenes"], "imagen"
    )
    videos_pendientes, videos_omitidos = filtrar_pendientes(
        archivos["videos"], "video"
    )

    total_omitidos  = imagenes_omitidas + videos_omitidos
    total_pendientes = len(imagenes_pendientes) + len(videos_pendientes)

    print(f"\n  📋  Pendientes de procesar : {total_pendientes}")
    print(f"  ⏭️   Ya existían en /salida : {total_omitidos}\n")

    # Si todos ya estaban procesados, terminar
    if total_pendientes == 0:
        print("  ✅  Todos los archivos ya fueron procesados anteriormente.")
        print("     Agrega nuevos archivos a /entradas para procesarlos.\n")
        sys.exit(0)

    # ── Paso 8: Procesar imágenes ──────────────────────────────────
    contadores_img = {"procesados": 0, "errores": 0}

    if imagenes_pendientes:
        imprimir_separador("PROCESANDO IMÁGENES")
        contadores_img = procesar_lote_imagenes(
            imagenes_pendientes,
            metodo,
            nombre_sticker
        )

    # ── Paso 9: Procesar videos ────────────────────────────────────
    contadores_vid = {"procesados": 0, "errores": 0}

    if videos_pendientes:
        imprimir_separador("PROCESANDO VIDEOS")
        contadores_vid = procesar_lote_videos(
            videos_pendientes,
            metodo,
            nombre_sticker
        )

    # ── Paso 10: Resumen final ─────────────────────────────────────
    total_procesados = contadores_img["procesados"] + contadores_vid["procesados"]
    total_errores    = contadores_img["errores"]    + contadores_vid["errores"]

    imprimir_resumen(total_procesados, total_omitidos, total_errores)

    if total_errores == 0:
        print("  🎉  ¡Proceso completado sin errores!")
    else:
        print("  ⚠️   Algunos archivos no pudieron procesarse.")
        print("      Revisa los mensajes anteriores para más detalles.")
    print()


# ─────────────────────────────────────────────
#  PUNTO DE ENTRADA DEL SISTEMA
#  Solo se ejecuta cuando corres: python main.py
#  No se ejecuta si este archivo es importado.
# ─────────────────────────────────────────────

if __name__ == "__main__":
    main()
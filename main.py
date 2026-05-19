import ctypes
import json
import os
import sys
import datetime

# ============================================================
#  CARGAR LIBRERIA C  (Windows: .dll  |  Linux: .so)
# ============================================================

BASE = os.path.dirname(os.path.abspath(__file__))

if sys.platform == "win32":
    lib_name = "trafico.dll"
else:
    # En Linux la convencion es libtrafico.so, pero si compilaste
    # con -o trafico.so puedes cambiar este valor a "trafico.so"
    lib_name = "libtrafico.so"

lib_path = os.path.join(BASE, lib_name)

if not os.path.exists(lib_path):
    print(f"ERROR: No se encontro la libreria '{lib_name}' en:\n  {BASE}")
    if sys.platform != "win32":
        print("\nPara compilarla en Debian/Linux ejecuta:")
        print("  gcc -shared -fPIC -o libtrafico.so trafico.c -lm")
    sys.exit(1)

dll = ctypes.CDLL(lib_path)

# ============================================================
#  ESTRUCTURAS — deben coincidir exactamente con trafico.h
# ============================================================

MAX_NODOS  = 200
MAX_NOMBRE = 64

class Camino(ctypes.Structure):
    _fields_ = [
        ("destino", ctypes.c_int),
        ("tiempo",  ctypes.c_float),
    ]

class Interseccion(ctypes.Structure):
    _fields_ = [
        ("nombre",       ctypes.c_char * MAX_NOMBRE),
        ("caminos",      Camino * MAX_NODOS),
        ("num_caminos",  ctypes.c_int),
        ("pos_x",        ctypes.c_float),
        ("pos_y",        ctypes.c_float),
    ]

class Grafo(ctypes.Structure):
    _fields_ = [
        ("intersecciones",    Interseccion * MAX_NODOS),
        ("num_intersecciones", ctypes.c_int),
    ]

class ResultadoRuta(ctypes.Structure):
    _fields_ = [
        ("ruta",           ctypes.c_int   * MAX_NODOS),
        ("longitud_ruta",  ctypes.c_int),
        ("distancias",     ctypes.c_float * MAX_NODOS),
        ("predecesores",   ctypes.c_int   * MAX_NODOS),
        ("origen",         ctypes.c_int),
        ("destino",        ctypes.c_int),
    ]

# ============================================================
#  CONFIGURAR TIPOS DE FUNCIONES C
# ============================================================

dll.inicializar_grafo.argtypes    = [ctypes.POINTER(Grafo)]
dll.inicializar_grafo.restype     = None

dll.agregar_interseccion.argtypes = [ctypes.POINTER(Grafo),
                                     ctypes.c_int,
                                     ctypes.c_char_p]
dll.agregar_interseccion.restype  = None

dll.agregar_camino.argtypes       = [ctypes.POINTER(Grafo),
                                     ctypes.c_int,
                                     ctypes.c_int,
                                     ctypes.c_float]
dll.agregar_camino.restype        = None

dll.evaluar_grafo.argtypes = [
    ctypes.POINTER(Grafo),
    ctypes.c_int,
    ctypes.c_int,
    ctypes.POINTER(ctypes.c_float),
    ctypes.POINTER(ctypes.c_float),
    ctypes.c_int
]
dll.evaluar_grafo.restype = ResultadoRuta

# ============================================================
#  LEER CONFIGURACION JSON
# ============================================================

def leer_config():
    with open(os.path.join(BASE, "config_visual.json"), "r", encoding="utf-8") as f:
        visual = json.load(f)
    with open(os.path.join(BASE, "config_sistema.json"), "r", encoding="utf-8") as f:
        sistema = json.load(f)
    return visual, sistema

# ============================================================
#  OBTENER FACTOR DE CONGESTION SEGUN HORA
# ============================================================

def obtener_factor_congestion(config_sistema):
    if config_sistema["sistema"]["hora_automatica"]:
        hora = datetime.datetime.now().hour
    else:
        hora = config_sistema["sistema"]["hora_actual"]

    franjas = config_sistema["congestion"]
    for nombre, franja in franjas.items():
        if nombre.startswith("_"):
            continue
        if franja["hora_inicio"] <= hora <= franja["hora_fin"]:
            print(f"  Hora: {hora}:00 — {franja['etiqueta']}"
                  f" (factor x{franja['factor']})")
            return franja["factor"]

    return 1.0  # factor neutro si no coincide ninguna franja

# ============================================================
#  LEER DATOS.TXT Y CONSTRUIR EL GRAFO
# ============================================================

def leer_datos(ruta_archivo, factor_congestion):
    nodos   = []   # lista de (id, nombre)
    aristas = []   # lista de (desde, hasta, tiempo)

    seccion_actual = None

    with open(ruta_archivo, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()

            # Ignorar comentarios y lineas vacias
            if not linea or linea.startswith("#"):
                continue

            # Detectar cambio de seccion
            if linea == "INTERSECCIONES:":
                seccion_actual = "intersecciones"
                continue
            if linea == "CAMINOS:":
                seccion_actual = "caminos"
                continue

            # Parsear segun seccion
            partes = [p.strip() for p in linea.split("|")]

            if seccion_actual == "intersecciones" and len(partes) == 2:
                nodo_id = int(partes[0])
                nombre  = partes[1]
                nodos.append((nodo_id, nombre))

            elif seccion_actual == "caminos" and len(partes) == 3:
                desde   = int(partes[0])
                hasta   = int(partes[1])
                tiempo  = float(partes[2]) * factor_congestion
                aristas.append((desde, hasta, tiempo))

    return nodos, aristas

# ============================================================
#  CONSTRUIR EL GRAFO EN C
# ============================================================

def construir_grafo(nodos, aristas):
    g = Grafo()
    dll.inicializar_grafo(ctypes.byref(g))

    for nodo_id, nombre in nodos:
        dll.agregar_interseccion(ctypes.byref(g),
                                 nodo_id,
                                 nombre.encode("utf-8"))

    for desde, hasta, tiempo in aristas:
        dll.agregar_camino(ctypes.byref(g),
                           desde,
                           hasta,
                           ctypes.c_float(tiempo))
    return g

# ============================================================
#  EXTRAER DATOS DEL GRAFO PARA EL HTML
# ============================================================

def extraer_datos_visualizacion(grafo, resultado, nodos):
    n = grafo.num_intersecciones

    # Nodos con posicion y estado
    nodos_html = []
    for i in range(n):
        inter = grafo.intersecciones[i]
        nodos_html.append({
            "id":     i,
            "nombre": inter.nombre.decode("utf-8"),
            "x":      round(inter.pos_x, 2),
            "y":      round(inter.pos_y, 2),
            "dist":   round(resultado.distancias[i], 1),
        })

    # Aristas sin duplicados (grafo no dirigido)
    aristas_html = []
    vistas = set()
    for i in range(n):
        inter = grafo.intersecciones[i]
        for j in range(inter.num_caminos):
            camino = inter.caminos[j]
            par = tuple(sorted((i, camino.destino)))
            if par not in vistas:
                vistas.add(par)
                aristas_html.append({
                    "desde":  par[0],
                    "hasta":  par[1],
                    "tiempo": round(camino.tiempo, 1),
                })

    # IDs que forman la ruta optima
    ruta_ids = list(resultado.ruta[:resultado.longitud_ruta])

    return nodos_html, aristas_html, ruta_ids

def leer_posiciones(config_sistema):
    with open(os.path.join(BASE, "config_posiciones.json"),
              "r", encoding="utf-8") as f:
        data = json.load(f)

    posiciones = data["posiciones"]
    n          = len(posiciones)
    pos_x      = (ctypes.c_float * n)()
    pos_y      = (ctypes.c_float * n)()

    for id_str, coords in posiciones.items():
        i        = int(id_str)
        pos_x[i] = coords["x"]
        pos_y[i] = coords["y"]

    return pos_x, pos_y, n

# ============================================================
#  ABRIR EL HTML EN EL NAVEGADOR (multiplataforma)
# ============================================================

def abrir_navegador(ruta_html):
    import subprocess
    if sys.platform == "win32":
        os.startfile(ruta_html)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", ruta_html])
    else:
        # Linux: intentar xdg-open, luego navegadores comunes como fallback
        navegadores = ["xdg-open", "firefox", "chromium", "chromium-browser", "google-chrome"]
        for nav in navegadores:
            try:
                subprocess.Popen([nav, ruta_html],
                                 stdout=subprocess.DEVNULL,
                                 stderr=subprocess.DEVNULL)
                return
            except FileNotFoundError:
                continue
        print(f"  No se pudo abrir el navegador automaticamente.")
        print(f"  Abre manualmente: {ruta_html}")

# ============================================================
#  PROGRAMA PRINCIPAL
# ============================================================

def main():
    print("\n" + "=" * 50)
    print("  SISTEMA DE TRAFICO URBANO")
    print("=" * 50)

    # Leer configuracion
    config_visual, config_sistema = leer_config()

    # Obtener factor de congestion segun hora
    factor = obtener_factor_congestion(config_sistema)

    # Leer datos.txt
    archivo_datos = os.path.join(BASE, "datos.txt")
    nodos, aristas = leer_datos(archivo_datos, factor)
    print(f"  Intersecciones cargadas: {len(nodos)}")
    print(f"  Caminos cargados:        {len(aristas)}")

    # Construir grafo en C
    grafo = construir_grafo(nodos, aristas)

    # Pedir origen y destino al usuario
    print("\n  Intersecciones disponibles:")
    for nodo_id, nombre in nodos:
        print(f"    {nodo_id} — {nombre}")

    print()
    origen  = int(input("  Ingresa el ID de origen:  "))
    destino = int(input("  Ingresa el ID de destino: "))

    # Llamar la funcion principal de C
    pos_x, pos_y, n_pos = leer_posiciones(config_sistema)

    resultado = dll.evaluar_grafo(ctypes.byref(grafo),
                               origen, destino,
                               pos_x, pos_y,
                               ctypes.c_int(n_pos))

    # Extraer datos para el HTML
    nodos_html, aristas_html, ruta_ids = extraer_datos_visualizacion(
        grafo, resultado, nodos
    )

    # Generar el HTML
    from generar_html import generar_html
    ruta_html = generar_html(nodos_html, aristas_html, ruta_ids,
                             origen, destino, resultado, config_visual)

    print("  Abriendo visualizacion en el navegador...")
    if ruta_html:
        abrir_navegador(ruta_html)
    print("=" * 50 + "\n")

if __name__ == "__main__":
    main()

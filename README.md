# Sistema de Tráfico Urbano con Dijkstra

Proyecto final de Estructuras de Datos — Universidad Tecnológica de Pereira  
Diego Alexander Neva Patiño · Jacobo Piedrahita Hurtado

---

## ¿De qué va esto?

La idea surgió de un problema concreto: ¿cómo sabe una app de navegación cuál camino es más rápido, si el tráfico cambia dependiendo de la hora? Decidimos implementarlo desde cero — grafo en C, lógica en Python, visualización en el navegador — sin librerías mágicas que hagan el trabajo sucio.

El sistema modela las intersecciones de Pereira como un grafo no dirigido ponderado. Dijkstra calcula la ruta más corta, pero los pesos no son fijos: a las 8am una vía puede costar el doble que a las 2am. Eso lo manejamos con factores de congestión configurables por franja horaria.

Si querés probar: de **Plaza de Bolívar** al **Aeropuerto Matecaña**, el sistema te da la ruta óptima en milisegundos y la muestra animada en el navegador.

---

## Archivos del proyecto

```
trafico_urbano/
├── datos.txt               ← el mapa de la ciudad, editable a mano
├── config_visual.json      ← colores y parámetros de animación
├── config_sistema.json     ← factores de congestión por hora
├── trafico.h               ← declaraciones en C
├── trafico.c               ← grafo + Dijkstra
├── trafico.dll             ← librería compilada (la generás vos con gcc)
├── main.py                 ← punto de entrada
├── generar_html.py         ← construye la visualización
└── grafo.html              ← se genera solo al ejecutar
```

---

## Cómo correrlo

**Requisitos:** Python 3, GCC (vía MSYS2 UCRT64), cualquier navegador.

```bash
# 1. Clonar
git clone https://github.com/tu-usuario/trafico-urbano.git
cd trafico-urbano

# 2. Compilar la librería (desde MSYS2 UCRT64)
gcc -shared -Wall -o trafico.dll trafico.c -lm

# 3. Ejecutar
python main.py
```

El programa lista las intersecciones, pedís origen y destino, y abre el grafo en el navegador automáticamente.

---

## Agregar intersecciones al mapa

`datos.txt` tiene un formato simple, no hace falta saber programar para editarlo:

```
INTERSECCIONES:
# ID | NOMBRE
20 | Mi Nueva Interseccion

CAMINOS:
# DESDE | HASTA | TIEMPO(minutos)
19 | 20 | 8
```

---

## Lo técnico

### El núcleo en C

Toda la lógica del grafo vive en `trafico.c`. Las estructuras principales:

```c
typedef struct {
    int   destino;
    float tiempo;
} Camino;

typedef struct {
    char   nombre[64];
    Camino caminos[200];
    int    num_caminos;
    float  pos_x, pos_y;
} Interseccion;

typedef struct {
    Interseccion intersecciones[200];
    int          num_intersecciones;
} Grafo;

typedef struct {
    int   ruta[200];
    int   longitud_ruta;
    float distancias[200];
    int   predecesores[200];
    int   origen, destino;
} ResultadoRuta;
```

Las funciones expuestas a Python:

| Función | Qué hace |
|---------|----------|
| `inicializar_grafo()` | Limpia memoria antes de cargar datos |
| `agregar_interseccion()` | Registra un nodo |
| `agregar_camino()` | Inserta arista bidireccional con validaciones |
| `dijkstra()` | Distancias mínimas desde el origen — O(V²) |
| `reconstruir_ruta()` | Recorre predecesores y devuelve la ruta |
| `evaluar_grafo()` | Función principal, retorna un `ResultadoRuta` |

### Puente C ↔ Python

Python no llama a un ejecutable sino directamente a la librería compilada usando `ctypes`:

```python
dll = ctypes.CDLL("trafico.dll")
dll.evaluar_grafo.restype = ResultadoRuta

resultado = dll.evaluar_grafo(
    ctypes.byref(grafo), origen, destino,
    pos_x, pos_y, n_pos
)
```

### Visualización con layout de fuerzas

El grafo se dibuja en un `<canvas>` HTML. En vez de posiciones fijas, usamos un simulador de fuerzas en JavaScript — los nodos se repelen entre sí, las aristas los atraen, y una gravedad central evita que todo se disperse. La simulación para sola cuando la energía converge, así funciona bien con 100+ nodos sin que quede ilegible.

### Factor de congestión

El peso real de cada arista se calcula en tiempo de ejecución:

```
peso_real = tiempo_base × factor(hora_actual)
```

Los factores están en `config_sistema.json` y se pueden cambiar sin tocar código:

| Franja | Factor | Por qué |
|--------|--------|---------|
| Madrugada (0–5h) | ×0.7 | Vías vacías |
| Pico mañana (6–9h) | ×2.5 | Todo el mundo sale al mismo tiempo |
| Mediodía (12–14h) | ×1.5 | Moderado |
| Pico tarde (17–20h) | ×2.8 | Lo peor del día |
| Noche (20–23h) | ×0.9 | Ya despejan |

---

## Personalización visual

`config_visual.json` controla colores y animación:

```json
{
  "nodos": {
    "color_normal":  "#4a90d9",
    "color_origen":  "#2ecc71",
    "color_destino": "#e74c3c",
    "color_en_ruta": "#f39c12"
  },
  "animacion": {
    "activar":      true,
    "velocidad_ms": 600
  }
}
```

---

## Interacción con el grafo

| Acción | Cómo |
|--------|------|
| Zoom | Rueda del mouse |
| Mover el mapa | Click y arrastrar |
| Reiniciar vista | Botón "Reiniciar zoom" |
| Pausar animación | Botón "Pausar animación" |

---

## Complejidad

| Operación | Complejidad |
|-----------|-------------|
| Insertar nodo | O(1) |
| Insertar arista | O(1) |
| Dijkstra (arreglo simple) | O(V²) |
| Reconstruir ruta | O(V) |
| Layout de fuerzas | O(V² × iteraciones) |

Para grafos grandes (500+ nodos) se puede mejorar Dijkstra con un min-heap y bajar a O((V+E) log V). Lo dejamos en la lista de pendientes.

---

## Cosas que quedaron pendientes

- Dijkstra con min-heap
- A* con heurística geográfica
- Leer datos desde OpenStreetMap
- Editor visual de nodos y aristas en el navegador
- Soporte para calles de un solo sentido

---

## Equipo

- Diego Alexander Neva Patiño  
- Jacobo Piedrahita Hurtado

Estructuras de Datos · Ingeniería de Sistemas · UTP · 2026
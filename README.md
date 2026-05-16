# 🚦 Sistema Integral de Tráfico Urbano + IA

> Proyecto de Estructuras de Datos — Universidad Tecnológica de Pereira  
> Diego Alexander Neva Patiño · Jacobo Piedrahita Hurtado  
> Grafo no dirigido ponderado con algoritmo de Dijkstra, visualización interactiva en navegador y factor de congestión inteligente por hora del día.

---

## 📸 Vista previa

![Vista del grafo interactivo](assets/preview.png)

> El sistema calcula la ruta óptima entre dos intersecciones y la muestra animada en el navegador. Los nodos se distribuyen automáticamente sin importar cuántos haya.

---

## ¿Qué hace este proyecto?

Imagina que estás en **Plaza de Bolívar** y quieres llegar al **Aeropuerto Matecana** de Pereira. Este sistema:

1. Lee el mapa de la ciudad desde un archivo de texto editable
2. Calcula automáticamente la ruta más rápida según el tráfico actual
3. Abre el navegador con el mapa animado e interactivo
4. Ajusta los tiempos según la hora del día — no es lo mismo viajar a las 8am que a las 2pm

Todo esto sin instalar nada extra más allá de Python y un compilador de C.

---

## 🗂️ Estructura del proyecto

```
trafico_urbano/
├── datos.txt               ← Mapa de la ciudad (editable por el usuario)
├── config_visual.json      ← Colores, tamaño de ventana, animación
├── config_sistema.json     ← Factor de congestión por hora del día
├── trafico.h               ← Declaraciones de estructuras y funciones en C
├── trafico.c               ← Lógica del grafo y algoritmo de Dijkstra en C
├── trafico.dll             ← Librería compilada (se genera con gcc)
├── main.py                 ← Programa principal en Python
├── generar_html.py         ← Genera la visualización interactiva
└── grafo.html              ← Se genera automáticamente al ejecutar
```

---

## 🚀 Guía rápida — Para usuarios

### 1. Requisitos

| Herramienta | Cómo obtenerla |
|-------------|---------------|
| Python 3.x  | [python.org](https://www.python.org/downloads/) |
| MSYS2 + GCC | [msys2.org](https://www.msys2.org/) → instalar `mingw-w64-ucrt-x86_64-gcc` |
| Navegador   | Chrome, Edge o Firefox (ya lo tienes) |

### 2. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/trafico-urbano.git
cd trafico-urbano
```

### 3. Compilar la librería C

Abre **MSYS2 UCRT64** y ejecuta:

```bash
cd /ruta/del/proyecto
gcc -shared -Wall -o trafico.dll trafico.c -lm
```

### 4. Ejecutar el sistema

```bash
python main.py
```

El programa mostrará las intersecciones disponibles, pedirá origen y destino, calculará la ruta óptima y abrirá el navegador automáticamente.

### 5. Personalizar el mapa

Abre `datos.txt` con cualquier editor de texto. El archivo tiene instrucciones claras adentro — puedes agregar intersecciones y caminos sin saber programar.

```
INTERSECCIONES:
# formato -> ID | NOMBRE
20 | Mi Nueva Interseccion

CAMINOS:
# formato -> DESDE | HASTA | TIEMPO(minutos)
19 | 20 | 8
```

---

## ⚙️ Guía técnica — Para desarrolladores

### Arquitectura del sistema

```
datos.txt + config_*.json
        ↓
      main.py
    ↙         ↘
trafico.dll   generar_html.py
  (C/ctypes)    (visualización)
        ↓
    grafo.html
        ↓
    navegador
```

### Capa C — `trafico.c`

Implementa la lógica central del sistema con las siguientes funciones:

| Función | Descripción |
|---------|-------------|
| `inicializar_grafo()` | Limpia la memoria antes de cargar datos |
| `agregar_interseccion()` | Registra un nodo con su ID y nombre |
| `agregar_camino()` | Inserta arista bidireccional con validaciones |
| `dijkstra()` | Calcula distancias mínimas desde el origen con complejidad $O(V^2)$ |
| `reconstruir_ruta()` | Recorre el arreglo de predecesores y devuelve la ruta en orden |
| `calcular_posiciones()` | Asigna coordenadas iniciales a los nodos |
| `evaluar_grafo()` | Función principal que une todo y retorna un `ResultadoRuta` |

### Estructuras de datos principales

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

### Puente C ↔ Python con `ctypes`

Python carga la librería compilada y llama las funciones C directamente:

```python
dll = ctypes.CDLL("trafico.dll")
dll.evaluar_grafo.restype = ResultadoRuta

resultado = dll.evaluar_grafo(
    ctypes.byref(grafo), origen, destino,
    pos_x, pos_y, n_pos
)
```

### Visualización — Layout de fuerzas

El grafo se renderiza en un `<canvas>` HTML con un algoritmo de layout de fuerzas implementado en JavaScript. Tres fuerzas actúan simultáneamente:

| Fuerza | Efecto |
|--------|--------|
| **Repulsión** entre nodos | Los separa para evitar solapamiento |
| **Atracción** por aristas | Acerca nodos conectados, longitud proporcional al peso |
| **Gravedad** al centro | Evita que los nodos se escapen del canvas |

La simulación se detiene automáticamente cuando la energía total del sistema converge. Esto permite escalar a **100+ nodos** sin degradación visual.

### Factor de congestión — IA

Los pesos de las aristas se multiplican dinámicamente según la hora del día:

```python
peso_real = tiempo_base × factor_congestión(hora_actual)
```

Los factores se configuran en `config_sistema.json`:

| Franja horaria | Factor | Efecto |
|---------------|--------|--------|
| Madrugada (0–5h) | ×0.7 | Vías libres |
| Mañana pico (6–9h) | ×2.5 | Tráfico alto |
| Mediodía (12–14h) | ×1.5 | Tráfico moderado |
| Tarde pico (17–20h) | ×2.8 | Máxima congestión |
| Noche (20–23h) | ×0.9 | Tráfico bajo |

### Compilación detallada

```bash
# Solo verificar sintaxis
gcc -Wall -Wextra -fsyntax-only trafico.c -lm

# Generar librería compartida
gcc -shared -Wall -o trafico.dll trafico.c -lm

# Verificar funciones exportadas
nm trafico.dll | grep -E "inicializar|agregar|dijkstra|reconstruir|calcular|evaluar"
```

---

## 🎨 Personalización visual

Edita `config_visual.json` para cambiar colores, tamaños y animación sin tocar el código:

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

## 🧩 Interactividad del grafo

| Acción | Cómo hacerlo |
|--------|-------------|
| Zoom | Rueda del mouse |
| Mover el grafo | Click y arrastrar |
| Reiniciar vista | Botón "Reiniciar zoom" |
| Pausar animación | Botón "Pausar animación" |

---

## 📊 Complejidad del algoritmo

| Operación | Complejidad |
|-----------|-------------|
| Insertar nodo | O(1) |
| Insertar arista | O(1) |
| Dijkstra (implementación actual) | O(V²) |
| Reconstruir ruta | O(V) |
| Layout de fuerzas (convergencia) | O(V² × iteraciones) |

> Para grafos grandes (500+ nodos) se puede mejorar Dijkstra usando una cola de prioridad (min-heap) para lograr O((V+E) log V).

---

## 🔧 Posibles mejoras futuras

- [ ] Implementar Dijkstra con min-heap para mejor rendimiento
- [ ] Agregar algoritmo A* con heurística geográfica
- [ ] Leer datos desde una API de tráfico real (Google Maps, OpenStreetMap)
- [ ] Interfaz web para agregar nodos y aristas visualmente sin editar el archivo
- [ ] Soporte para calles de un solo sentido (grafo dirigido)
- [ ] Exportar la ruta como archivo de texto o imagen

---

## 👥 Equipo

- Diego Alexander Neva Patiño
- Jacobo Piedrahita Hurtado

---

## 🏛️ Información académica

| | |
|--|--|
| **Universidad** | Universidad Tecnológica de Pereira |
| **Curso** | Estructuras de Datos |
| **Programa** | Ingeniería de Sistemas |
| **Año** | 2025 |

---

## 📄 Licencia

Este proyecto fue desarrollado con fines académicos para la Universidad Tecnológica de Pereira.

---

<div align="center">
  <sub>Hecho con C, Python y JavaScript · Universidad Tecnológica de Pereira · 2025</sub>
</div>

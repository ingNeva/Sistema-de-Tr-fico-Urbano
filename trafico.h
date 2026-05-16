#ifndef TRAFICO_H
#define TRAFICO_H

// ============================================================
//  CONSTANTES
// ============================================================

#define MAX_NODOS    200     // maximo de intersecciones
#define MAX_NOMBRE    64     // maximo de caracteres en un nombre
#define INF        99999     // representa "sin conexion"

// ============================================================
//  ESTRUCTURAS
// ============================================================

/*
 * Camino: representa una conexion entre dos intersecciones.
 * Es un elemento de la lista de adyacencia de cada nodo.
 */
typedef struct {
    int   destino;           // ID de la interseccion de llegada
    float tiempo;            // tiempo en minutos para recorrerlo
} Camino;

/*
 * Interseccion: un punto del mapa (esquina, parque, edificio).
 * Guarda su nombre y la lista de caminos que salen de ella.
 */
typedef struct {
    char   nombre[MAX_NOMBRE]; // nombre legible de la interseccion
    Camino caminos[MAX_NODOS]; // lista de caminos hacia vecinos
    int    num_caminos;        // cuantos caminos tiene esta interseccion
    float  pos_x;             // posicion X calculada para visualizar
    float  pos_y;             // posicion Y calculada para visualizar
} Interseccion;

/*
 * Grafo: el mapa completo de la ciudad.
 * Contiene todas las intersecciones y sus conexiones.
 */
typedef struct {
    Interseccion intersecciones[MAX_NODOS]; // arreglo de nodos
    int          num_intersecciones;        // cuantas hay en total
} Grafo;

/*
 * ResultadoRuta: lo que devuelve evaluar_grafo().
 * Contiene toda la informacion calculada desde el origen.
 */
typedef struct {
    int   ruta[MAX_NODOS];          // secuencia de IDs de la ruta optima
    int   longitud_ruta;            // cuantos nodos tiene la ruta
    float distancias[MAX_NODOS];    // tiempo minimo a cada interseccion
    int   predecesores[MAX_NODOS];  // nodo anterior en la ruta optima
    int   origen;                   // desde donde se calculo todo
    int   destino;                  // hasta donde se quiere llegar
} ResultadoRuta;

// ============================================================
//  FUNCIONES — declaraciones
// ============================================================

/* Inicializa el grafo vacio antes de agregar datos */
void inicializar_grafo(Grafo* g);

/* Agrega una interseccion al grafo con su nombre */
void agregar_interseccion(Grafo* g, int id, const char* nombre);

/* Agrega un camino bidireccional entre dos intersecciones */
void agregar_camino(Grafo* g, int desde, int hasta, float tiempo);

/* Calcula las posiciones X,Y de cada nodo para visualizarlos
   distribuidos en un circulo segun el numero de intersecciones */
void calcular_posiciones(Grafo* g, float* pos_x, float* pos_y, int n_pos);

/* Ejecuta Dijkstra desde el origen y retorna rutas y distancias */
void dijkstra(Grafo* g, int origen, float* distancias, int* predecesores);

/* Reconstruye la ruta desde origen hasta destino
   usando el arreglo de predecesores de Dijkstra */
void reconstruir_ruta(int* predecesores, int origen, int destino,
                      int* ruta, int* longitud_ruta);

/* Funcion principal: evalua el grafo desde un origen hacia un destino.
   Llama a dijkstra() + reconstruir_ruta() y llena el ResultadoRuta */
ResultadoRuta evaluar_grafo(Grafo* g, int origen, int destino,
                            float* pos_x, float* pos_y, int n_pos);

#endif // TRAFICO_H
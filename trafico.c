#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "trafico.h"

// ============================================================
//  INICIALIZAR GRAFO
//  Debe llamarse siempre antes de agregar cualquier dato.
//  Pone todos los contadores en 0 y limpia la memoria.
// ============================================================

void inicializar_grafo(Grafo* g) {
    g->num_intersecciones = 0;

    for (int i = 0; i < MAX_NODOS; i++) {
        g->intersecciones[i].num_caminos = 0;
        g->intersecciones[i].pos_x       = 0.0f;
        g->intersecciones[i].pos_y       = 0.0f;
        memset(g->intersecciones[i].nombre, 0, MAX_NOMBRE);
    }
}

// ============================================================
//  AGREGAR INTERSECCION
//  Registra una interseccion nueva con su ID y nombre.
//  Si el ID ya existe, actualiza el nombre.
// ============================================================

void agregar_interseccion(Grafo* g, int id, const char* nombre) {

    // Validar que el ID este dentro del rango permitido
    if (id < 0 || id >= MAX_NODOS) {
        fprintf(stderr, "Error: ID %d fuera de rango (0 - %d)\n",
                id, MAX_NODOS - 1);
        return;
    }

    // Copiar el nombre con limite para no desbordar el buffer
    strncpy(g->intersecciones[id].nombre, nombre, MAX_NOMBRE - 1);
    g->intersecciones[id].nombre[MAX_NOMBRE - 1] = '\0';

    // Actualizar el contador si es una interseccion nueva
    if (id >= g->num_intersecciones)
        g->num_intersecciones = id + 1;
}

// ============================================================
//  AGREGAR CAMINO
//  Conecta dos intersecciones en ambas direcciones (no dirigido).
//  Si alguno de los IDs no existe o el tiempo es invalido,
//  imprime un error y no agrega nada.
// ============================================================

void agregar_camino(Grafo* g, int desde, int hasta, float tiempo) {

    // Validar IDs
    if (desde < 0 || desde >= g->num_intersecciones ||
        hasta < 0 || hasta >= g->num_intersecciones) {
        fprintf(stderr,
                "Error: camino (%d -> %d) usa IDs que no existen\n",
                desde, hasta);
        return;
    }

    // Validar que el tiempo sea positivo
    if (tiempo <= 0) {
        fprintf(stderr,
                "Error: el tiempo del camino (%d -> %d) debe ser mayor a 0\n",
                desde, hasta);
        return;
    }

    // Validar que no se supere el maximo de caminos por nodo
    if (g->intersecciones[desde].num_caminos >= MAX_NODOS ||
        g->intersecciones[hasta].num_caminos >= MAX_NODOS) {
        fprintf(stderr,
                "Error: interseccion %d o %d tiene demasiados caminos\n",
                desde, hasta);
        return;
    }

    // Agregar direccion desde -> hasta
    int nc_desde = g->intersecciones[desde].num_caminos;
    g->intersecciones[desde].caminos[nc_desde].destino = hasta;
    g->intersecciones[desde].caminos[nc_desde].tiempo  = tiempo;
    g->intersecciones[desde].num_caminos++;

    // Agregar direccion hasta -> desde (no dirigido)
    int nc_hasta = g->intersecciones[hasta].num_caminos;
    g->intersecciones[hasta].caminos[nc_hasta].destino = desde;
    g->intersecciones[hasta].caminos[nc_hasta].tiempo  = tiempo;
    g->intersecciones[hasta].num_caminos++;
}
// ============================================================
//  DIJKSTRA
//  Calcula el tiempo minimo desde el origen hasta todas las
//  demas intersecciones del grafo.
//
//  Parametros:
//    g            -> el grafo completo
//    origen       -> ID de la interseccion de partida
//    distancias   -> arreglo de salida: tiempo minimo a cada nodo
//    predecesores -> arreglo de salida: nodo anterior en la ruta
//
//  Ambos arreglos deben tener tamaño MAX_NODOS y ser
//  reservados por quien llama la funcion.
// ============================================================

void dijkstra(Grafo* g, int origen,
              float* distancias, int* predecesores) {

    int   visitado[MAX_NODOS];
    int   n = g->num_intersecciones;

    // ── Inicializar arreglos ─────────────────────────────────
    for (int i = 0; i < n; i++) {
        distancias[i]   = INF;   // aun no sabemos como llegar
        predecesores[i] = -1;    // sin predecesor conocido
        visitado[i]     = 0;     // ninguno visitado aun
    }
    distancias[origen] = 0.0f;   // llegar al origen cuesta 0

    // ── Ciclo principal ──────────────────────────────────────
    // En cada iteracion procesamos el nodo no visitado
    // con la menor distancia acumulada conocida hasta ahora.

    for (int iter = 0; iter < n; iter++) {

        // Buscar el nodo no visitado con menor distancia
        int   u    = -1;
        float menor = INF;

        for (int i = 0; i < n; i++) {
            if (!visitado[i] && distancias[i] < menor) {
                menor = distancias[i];
                u     = i;
            }
        }

        // Si no encontramos ningun nodo alcanzable, terminamos
        if (u == -1) break;

        // Marcar como visitado — ya no cambiara su distancia
        visitado[u] = 1;

        // ── Relajacion de caminos ────────────────────────────
        // Para cada vecino de u, verificamos si pasar por u
        // ofrece un camino mas corto que el que ya conocemos.

        int num_caminos = g->intersecciones[u].num_caminos;

        for (int j = 0; j < num_caminos; j++) {

            int   v        = g->intersecciones[u].caminos[j].destino;
            float tiempo_v = g->intersecciones[u].caminos[j].tiempo;

            // Solo relajar si v no fue visitado aun
            if (visitado[v]) continue;

            float nueva_dist = distancias[u] + tiempo_v;

            // Si encontramos un camino mas corto, actualizamos
            if (nueva_dist < distancias[v]) {
                distancias[v]   = nueva_dist;
                predecesores[v] = u;  // venimos desde u
            }
        }
    }
}
// ============================================================
//  RECONSTRUIR RUTA
//  Usa el arreglo de predecesores que deja Dijkstra para
//  armar la secuencia de intersecciones desde origen a destino.
//
//  Parametros:
//    predecesores  -> arreglo generado por dijkstra()
//    origen        -> ID de inicio
//    destino       -> ID de llegada
//    ruta          -> arreglo de salida con los IDs en orden
//    longitud_ruta -> cuantos nodos tiene la ruta resultante
//
//  Si no existe ruta entre origen y destino,
//  longitud_ruta queda en 0.
// ============================================================

void reconstruir_ruta(int* predecesores, int origen, int destino,
                      int* ruta, int* longitud_ruta) {

    *longitud_ruta = 0;

    // Verificar que el destino sea alcanzable
    // Si su predecesor es -1 y no es el origen, no hay ruta
    if (predecesores[destino] == -1 && destino != origen) {
        fprintf(stderr,
                "Aviso: no existe ruta entre %d y %d\n",
                origen, destino);
        return;
    }

    // ── Recorrer predecesores de destino hacia origen ────────
    // Guardamos los nodos en orden inverso primero
    int temporal[MAX_NODOS];
    int contador = 0;
    int actual   = destino;

    while (actual != -1) {
        temporal[contador++] = actual;
        actual = predecesores[actual];

        // Proteccion contra ciclos inesperados
        if (contador > MAX_NODOS) {
            fprintf(stderr, "Error: ciclo detectado al reconstruir ruta\n");
            *longitud_ruta = 0;
            return;
        }
    }

    // ── Invertir el arreglo temporal ─────────────────────────
    // Ahora queda en orden correcto: origen -> ... -> destino
    for (int i = 0; i < contador; i++)
        ruta[i] = temporal[contador - 1 - i];

    *longitud_ruta = contador;
}
// ============================================================
//  CALCULAR POSICIONES
//  Lee las posiciones X,Y desde un arreglo externo que
//  Python carga del config_posiciones.json y pasa a C.
//
//  Parametros:
//    g      -> el grafo con las intersecciones cargadas
//    pos_x  -> arreglo de coordenadas X por ID de nodo
//    pos_y  -> arreglo de coordenadas Y por ID de nodo
//    n_pos  -> cuantas posiciones trae el arreglo
// ============================================================

void calcular_posiciones(Grafo* g, float* pos_x, float* pos_y, int n_pos) {
    int n = g->num_intersecciones;

    for (int i = 0; i < n; i++) {
        if (i < n_pos) {
            // Usar coordenada del JSON
            g->intersecciones[i].pos_x = pos_x[i];
            g->intersecciones[i].pos_y = pos_y[i];
        } else {
            // Fallback: posicion en circulo si no tiene coordenada
            float angulo = i * (2.0f * 3.14159265f / n);
            g->intersecciones[i].pos_x = 450 + 300 * cosf(angulo);
            g->intersecciones[i].pos_y = 300 + 200 * sinf(angulo);
        }
    }
}

// ============================================================
//  EVALUAR GRAFO  ← funcion principal que llama Python
//  Recibe el grafo ya construido, un origen y un destino.
//  Internamente llama a calcular_posiciones(), dijkstra()
//  y reconstruir_ruta(), y empaqueta todo en un ResultadoRuta.
//
//  Parametros:
//    g       -> el grafo completo con intersecciones y caminos
//    origen  -> ID de la interseccion de partida
//    destino -> ID de la interseccion de llegada
//
//  Retorna:
//    ResultadoRuta con ruta optima, distancias y posiciones
// ============================================================

ResultadoRuta evaluar_grafo(Grafo* g, int origen, int destino,
                            float* pos_x, float* pos_y, int n_pos) {
    ResultadoRuta resultado;
    int n = g->num_intersecciones;

    memset(&resultado, 0, sizeof(ResultadoRuta));
    resultado.origen  = origen;
    resultado.destino = destino;

    if (origen  < 0 || origen  >= n ||
        destino < 0 || destino >= n) {
        fprintf(stderr,
                "Error: origen %d o destino %d fuera de rango\n",
                origen, destino);
        resultado.longitud_ruta = 0;
        return resultado;
    }

    calcular_posiciones(g, pos_x, pos_y, n_pos);
    dijkstra(g, origen, resultado.distancias, resultado.predecesores);
    reconstruir_ruta(resultado.predecesores, origen, destino,
                     resultado.ruta, &resultado.longitud_ruta);

    printf("\n  Origen:  %s\n", g->intersecciones[origen].nombre);
    printf("  Destino: %s\n",  g->intersecciones[destino].nombre);
    printf("  Ruta optima:\n");
    for (int i = 0; i < resultado.longitud_ruta; i++) {
        int id = resultado.ruta[i];
        if (i == 0)
            printf("    %s\n",     g->intersecciones[id].nombre);
        else
            printf("    -> %s\n",  g->intersecciones[id].nombre);
    }
    if (resultado.longitud_ruta > 0)
        printf("  Tiempo total: %.1f minutos\n\n",
               resultado.distancias[destino]);
    else
        printf("  Sin ruta disponible.\n\n");

    return resultado;
}
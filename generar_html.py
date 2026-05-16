import json
import os
import webbrowser

BASE = os.path.dirname(os.path.abspath(__file__))

# ============================================================
#  GENERAR HTML
# ============================================================

def generar_html(nodos, aristas, ruta_ids,
                 origen, destino, resultado, config_visual):

    # Leer configuracion visual
    v         = config_visual
    ancho     = v["ventana"]["ancho"]
    alto      = v["ventana"]["alto"]
    titulo    = v["ventana"]["titulo"]
    fondo     = v["ventana"]["fondo"]

    c_normal  = v["caminos"]["color_normal"]
    c_ruta    = v["caminos"]["color_en_ruta"]
    g_normal  = v["caminos"]["grosor_normal"]
    g_ruta    = v["caminos"]["grosor_en_ruta"]
    mostrar_w = str(v["caminos"]["mostrar_pesos"]).lower()
    c_peso    = v["caminos"]["color_peso"]
    t_peso    = v["caminos"]["tamano_peso"]

    n_radio   = v["nodos"]["radio"]
    n_normal  = v["nodos"]["color_normal"]
    n_origen  = v["nodos"]["color_origen"]
    n_destino = v["nodos"]["color_destino"]
    n_ruta    = v["nodos"]["color_en_ruta"]
    n_texto   = v["nodos"]["color_texto"]
    t_texto   = v["nodos"]["tamano_texto"]

    anim_on   = str(v["animacion"]["activar"]).lower()
    anim_ms   = v["animacion"]["velocidad_ms"]
    c_activo  = v["animacion"]["color_nodo_activo"]

    # Tiempo total de la ruta
    tiempo_total = round(resultado.distancias[destino], 1)
    nombre_origen  = nodos[origen]["nombre"]
    nombre_destino = nodos[destino]["nombre"]

    # Serializar datos para JavaScript
    nodos_json   = json.dumps(nodos,   ensure_ascii=False)
    aristas_json = json.dumps(aristas, ensure_ascii=False)
    ruta_json    = json.dumps(ruta_ids)

    # ── Generar HTML ─────────────────────────────────────────
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{titulo}</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}

    body {{
      background: #0f0f1a;
      font-family: 'Segoe UI', sans-serif;
      color: #ffffff;
      display: flex;
      flex-direction: column;
      align-items: center;
      min-height: 100vh;
      padding: 20px;
    }}

    h1 {{
      font-size: 20px;
      font-weight: 500;
      color: #aaaacc;
      margin-bottom: 6px;
      letter-spacing: 1px;
    }}

    .ruta-info {{
      font-size: 14px;
      color: #ffffff;
      margin-bottom: 14px;
      text-align: center;
    }}

    .ruta-info span {{
      color: {n_ruta};
      font-weight: 600;
    }}

    canvas {{
      background: {fondo};
      border-radius: 12px;
      box-shadow: 0 4px 32px rgba(0,0,0,0.5);
      cursor: grab;
    }}

    canvas:active {{ cursor: grabbing; }}

    .panel {{
      margin-top: 16px;
      background: #1e1e30;
      border-radius: 10px;
      padding: 14px 20px;
      width: {ancho}px;
      display: flex;
      gap: 20px;
      flex-wrap: wrap;
    }}

    .panel-seccion {{
      flex: 1;
      min-width: 200px;
    }}

    .panel-titulo {{
      font-size: 12px;
      color: #aaaacc;
      text-transform: uppercase;
      letter-spacing: 1px;
      margin-bottom: 8px;
      border-bottom: 1px solid #2a2a44;
      padding-bottom: 4px;
    }}

    .dist-item {{
      display: flex;
      justify-content: space-between;
      font-size: 12px;
      padding: 3px 0;
      color: #ccccee;
      border-bottom: 1px solid #1a1a2a;
    }}

    .dist-item.en-ruta {{
      color: {n_ruta};
      font-weight: 600;
    }}

    .dist-item.origen  {{ color: {n_origen};  font-weight: 700; }}
    .dist-item.destino {{ color: {n_destino}; font-weight: 700; }}

    .controles {{
      display: flex;
      gap: 10px;
      margin-top: 14px;
    }}

    button {{
      background: #2a2a44;
      color: #ccccee;
      border: 1px solid #3a3a5a;
      border-radius: 6px;
      padding: 7px 16px;
      font-size: 12px;
      cursor: pointer;
      transition: background 0.2s;
    }}

    button:hover {{ background: #3a3a5a; }}
    button.activo {{ background: {n_ruta}; color: #000; }}
  </style>
</head>
<body>

<h1>{titulo.upper()}</h1>
<div class="ruta-info">
  <span>{nombre_origen}</span>
  &nbsp;→&nbsp;
  <span>{nombre_destino}</span>
  &nbsp;·&nbsp;
  Tiempo óptimo: <span>{tiempo_total} min</span>
</div>

<canvas id="canvas" width="{ancho}" height="{alto}"></canvas>

<div class="controles">
  <button id="btnAnimar" class="activo" onclick="toggleAnimacion()">⏸ Pausar animación</button>
  <button onclick="resetZoom()">⟳ Reiniciar zoom</button>
</div>

<div class="panel">
  <div class="panel-seccion">
    <div class="panel-titulo">Ruta óptima</div>
    <div id="lista-ruta"></div>
  </div>
  <div class="panel-seccion">
    <div class="panel-titulo">Distancias desde {nombre_origen}</div>
    <div id="lista-distancias"></div>
  </div>
</div>

<script>
// ── Datos desde Python ──────────────────────────────────────
const NODOS   = {nodos_json};
const ARISTAS = {aristas_json};
const RUTA    = {ruta_json};
const ORIGEN  = {origen};
const DESTINO = {destino};

const CFG = {{
  colorNormal:  "{c_normal}",
  colorRuta:    "{c_ruta}",
  grosorNormal:  {g_normal},
  grosorRuta:    {g_ruta},
  mostrarPesos:  {mostrar_w},
  colorPeso:    "{c_peso}",
  tamPeso:       {t_peso},
  nRadio:        {n_radio},
  nNormal:      "{n_normal}",
  nOrigen:      "{n_origen}",
  nDestino:     "{n_destino}",
  nRuta:        "{n_ruta}",
  nTexto:       "{n_texto}",
  tamTexto:      {t_texto},
  animOn:        {anim_on},
  animMs:        {anim_ms},
  cActivo:      "{c_activo}",
}};

// ── Canvas y estado ─────────────────────────────────────────
const canvas  = document.getElementById("canvas");
const ctx     = canvas.getContext("2d");
const W       = canvas.width;
const H       = canvas.height;
const rutaSet = new Set(RUTA);

let animando     = CFG.animOn;
let pasoActual   = 0;
let ultimoTiempo = 0;
let offsetX = 0, offsetY = 0, escala = 1;
let dragging = false, lastX, lastY;
let simulando = true;   // el layout de fuerzas sigue corriendo

// ── Posiciones iniciales — distribuir en grid ───────────────
// Partimos de un grid regular para que la simulacion
// converja mas rapido que desde posiciones aleatorias
const cols = Math.ceil(Math.sqrt(NODOS.length * 1.6));
const cellW = W / (cols + 1);
const cellH = H / (Math.ceil(NODOS.length / cols) + 1);

NODOS.forEach((n, i) => {{
  n.vx = 0;
  n.vy = 0;
  n.fx = (i % cols + 1) * cellW + (Math.random() - 0.5) * 30;
  n.fy = (Math.floor(i / cols) + 1) * cellH + (Math.random() - 0.5) * 30;
}});

// ── Layout de fuerzas ───────────────────────────────────────
// Cada tick aplica tres fuerzas:
//   1. Repulsion entre nodos       (se empujan entre si)
//   2. Atraccion por aristas       (los conectados se acercan)
//   3. Gravedad al centro          (evita que se escapen)

function tickFuerzas() {{
  if (!simulando) return;

  const K_repulsion = 8000;   // fuerza de repulsion entre nodos
  const K_arista    = 0.03;   // fuerza de atraccion por arista
  const K_gravedad  = 0.015;  // fuerza hacia el centro
  const amort       = 0.85;   // amortiguacion de velocidad
  const distMin     = 60;     // distancia minima entre nodos

  // Resetear fuerzas acumuladas
  NODOS.forEach(n => {{ n.ax = 0; n.ay = 0; }});

  // 1. Repulsion entre cada par de nodos
  for (let i = 0; i < NODOS.length; i++) {{
    for (let j = i + 1; j < NODOS.length; j++) {{
      const a  = NODOS[i];
      const b  = NODOS[j];
      let dx   = a.fx - b.fx;
      let dy   = a.fy - b.fy;
      let dist = Math.sqrt(dx * dx + dy * dy) || 0.01;

      // Fuerza mas fuerte si estan muy cerca
      if (dist < distMin) dist = distMin;

      const f  = K_repulsion / (dist * dist);
      const fx = (dx / dist) * f;
      const fy = (dy / dist) * f;

      a.ax += fx;  a.ay += fy;
      b.ax -= fx;  b.ay -= fy;
    }}
  }}

  // 2. Atraccion por aristas (muelle)
  ARISTAS.forEach(ar => {{
    const a  = NODOS[ar.desde];
    const b  = NODOS[ar.hasta];
    const dx = b.fx - a.fx;
    const dy = b.fy - a.fy;
    const dist = Math.sqrt(dx * dx + dy * dy) || 0.01;

    // Longitud ideal de arista segun peso
    const ideal = 80 + ar.tiempo * 6;
    const f     = (dist - ideal) * K_arista;
    const fx    = (dx / dist) * f;
    const fy    = (dy / dist) * f;

    a.ax += fx;  a.ay += fy;
    b.ax -= fx;  b.ay -= fy;
  }});

  // 3. Gravedad suave hacia el centro del canvas
  NODOS.forEach(n => {{
    n.ax += (W / 2 - n.fx) * K_gravedad;
    n.ay += (H / 2 - n.fy) * K_gravedad;
  }});

  // Aplicar fuerzas → velocidad → posicion
  let energiaTotal = 0;
  NODOS.forEach(n => {{
    n.vx = (n.vx + n.ax) * amort;
    n.vy = (n.vy + n.ay) * amort;
    n.fx += n.vx;
    n.fy += n.vy;

    // Mantener dentro del canvas con margen
    const m = CFG.nRadio + 10;
    n.fx = Math.max(m, Math.min(W - m, n.fx));
    n.fy = Math.max(m, Math.min(H - m, n.fy));

    energiaTotal += Math.abs(n.vx) + Math.abs(n.vy);
  }});

  // Detener simulacion cuando el grafo convergio
  if (energiaTotal < 0.5) simulando = false;
}}

// ── Zoom y paneo ────────────────────────────────────────────
canvas.addEventListener("wheel", e => {{
  e.preventDefault();
  const factor = e.deltaY < 0 ? 1.1 : 0.9;
  escala = Math.min(Math.max(escala * factor, 0.3), 4);
  dibujar();
}});
canvas.addEventListener("mousedown", e => {{
  dragging = true; lastX = e.offsetX; lastY = e.offsetY;
}});
canvas.addEventListener("mousemove", e => {{
  if (!dragging) return;
  offsetX += e.offsetX - lastX;
  offsetY += e.offsetY - lastY;
  lastX = e.offsetX; lastY = e.offsetY;
  dibujar();
}});
canvas.addEventListener("mouseup",   () => dragging = false);
canvas.addEventListener("mouseleave",() => dragging = false);

function resetZoom() {{
  offsetX = 0; offsetY = 0; escala = 1; dibujar();
}}

// ── Helpers ─────────────────────────────────────────────────
function posNodo(n) {{
  return {{
    x: n.fx * escala + offsetX,
    y: n.fy * escala + offsetY,
  }};
}}

function esEnRuta(id) {{ return rutaSet.has(id); }}

function colorNodo(id) {{
  if (id === ORIGEN)  return CFG.nOrigen;
  if (id === DESTINO) return CFG.nDestino;
  if (esEnRuta(id))   return CFG.nRuta;
  return CFG.nNormal;
}}

// ── Dibujar ─────────────────────────────────────────────────
function dibujar(pasoAnim) {{
  ctx.clearRect(0, 0, W, H);

  // Aristas
  ARISTAS.forEach(a => {{
    const desde = posNodo(NODOS[a.desde]);
    const hasta = posNodo(NODOS[a.hasta]);

    const enRuta = esEnRuta(a.desde) && esEnRuta(a.hasta) &&
      Math.abs(RUTA.indexOf(a.desde) - RUTA.indexOf(a.hasta)) === 1;

    ctx.beginPath();
    ctx.moveTo(desde.x, desde.y);
    ctx.lineTo(hasta.x, hasta.y);
    ctx.strokeStyle = enRuta ? CFG.colorRuta : CFG.colorNormal;
    ctx.lineWidth   = (enRuta ? CFG.grosorRuta : CFG.grosorNormal) * escala;
    ctx.stroke();

    if (CFG.mostrarPesos) {{
      const mx = (desde.x + hasta.x) / 2;
      const my = (desde.y + hasta.y) / 2;
      ctx.fillStyle    = CFG.colorPeso;
      ctx.font         = `${{Math.max(9, CFG.tamPeso * escala)}}px Segoe UI`;
      ctx.textAlign    = "center";
      ctx.fillText(a.tiempo, mx, my - 4 * escala);
    }}
  }});

  // Nodos
  NODOS.forEach(n => {{
    const p      = posNodo(n);
    const radio  = CFG.nRadio * escala;
    const activo = pasoAnim !== undefined && n.id === RUTA[pasoAnim];

    if (activo) {{
      ctx.beginPath();
      ctx.arc(p.x, p.y, radio * 1.6, 0, Math.PI * 2);
      ctx.fillStyle = CFG.cActivo + "55";
      ctx.fill();
    }}

    ctx.beginPath();
    ctx.arc(p.x, p.y, radio, 0, Math.PI * 2);
    ctx.fillStyle   = activo ? CFG.cActivo : colorNodo(n.id);
    ctx.fill();
    ctx.strokeStyle = "#ffffff22";
    ctx.lineWidth   = 1;
    ctx.stroke();

    // Nombre — se adapta al zoom
    const tamTexto = Math.max(8, CFG.tamTexto * escala);
    ctx.fillStyle    = CFG.nTexto;
    ctx.font         = `bold ${{tamTexto}}px Segoe UI`;
    ctx.textAlign    = "center";
    ctx.textBaseline = "middle";

    // Partir nombre en dos lineas si es largo
    const palabras = n.nombre.split(" ");
    if (palabras.length > 2 && radio > 18) {{
      const linea1 = palabras.slice(0, Math.ceil(palabras.length/2)).join(" ");
      const linea2 = palabras.slice(Math.ceil(palabras.length/2)).join(" ");
      ctx.fillText(linea1, p.x, p.y - tamTexto * 0.6);
      ctx.fillText(linea2, p.x, p.y + tamTexto * 0.6);
    }} else {{
      const nombre = n.nombre.length > 12
        ? n.nombre.substring(0, 11) + "…"
        : n.nombre;
      ctx.fillText(nombre, p.x, p.y);
    }}
  }});
}}

// ── Loop principal ───────────────────────────────────────────
function loop(timestamp) {{
  tickFuerzas();

  if (animando && RUTA.length > 0) {{
    if (timestamp - ultimoTiempo > CFG.animMs) {{
      ultimoTiempo = timestamp;
      pasoActual   = (pasoActual + 1) % RUTA.length;
    }}
    dibujar(pasoActual);
  }} else {{
    dibujar();
  }}
  requestAnimationFrame(loop);
}}

function toggleAnimacion() {{
  animando = !animando;
  const btn = document.getElementById("btnAnimar");
  btn.textContent = animando ? "⏸ Pausar animación" : "▶ Reanudar animación";
  btn.className   = animando ? "activo" : "";
}}

// ── Panel de informacion ─────────────────────────────────────
function llenarPanel() {{
  const divRuta = document.getElementById("lista-ruta");
  RUTA.forEach((id, i) => {{
    const n   = NODOS[id];
    const div = document.createElement("div");
    div.className = "dist-item en-ruta";
    div.innerHTML = `<span>${{i===0?"🟢":i===RUTA.length-1?"🔴":"→"}} ${{n.nombre}}</span>
                     <span>${{n.dist}} min</span>`;
    divRuta.appendChild(div);
  }});

  const divDist = document.getElementById("lista-distancias");
  NODOS.forEach(n => {{
    const div = document.createElement("div");
    let cls = "dist-item";
    if (n.id === ORIGEN)  cls += " origen";
    if (n.id === DESTINO) cls += " destino";
    if (esEnRuta(n.id))   cls += " en-ruta";
    div.className = cls;
    div.innerHTML = `<span>${{n.nombre}}</span>
                     <span>${{n.dist >= 99999 ? "∞" : n.dist+" min"}}</span>`;
    divDist.appendChild(div);
  }});
}}

llenarPanel();
requestAnimationFrame(loop);
</script>
</body>
</html>"""

    # Guardar el archivo
    ruta_html = os.path.join(BASE, "grafo.html")
    with open(ruta_html, "w", encoding="utf-8") as f:
        f.write(html)

    # Abrir automaticamente en el navegador
    webbrowser.open(f"file:///{ruta_html.replace(os.sep, '/')}")
    print(f"  HTML generado: grafo.html")
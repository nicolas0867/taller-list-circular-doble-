"""
Taller: LISTAS CIRCULARES DOBLES - Caso de estudio: Rutina de ejercicios (version WEB)
Ejecutar:  python3 rutina_web.py   (se abre el navegador en http://localhost:8000)
Solo usa la libreria estandar de Python, no hay que instalar nada.
"""
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer


# ----------------------------------------------------------------------
# ESTRUCTURA DE DATOS: LISTA CIRCULAR DOBLE
# Cada nodo es un diccionario:
#   {"nombre":..., "duracion":..., "series":..., "siguiente":nodo, "anterior":nodo}
# ----------------------------------------------------------------------
def crear_nodo(nombre, duracion, series):
    return {"nombre": nombre, "duracion": duracion, "series": series,
            "siguiente": None, "anterior": None}


class ListaCircularDoble:
    def __init__(self):
        self.cabeza = None
        self.actual = None
        self.tamano = 0

    def insertar_final(self, nombre, duracion, series):
        nuevo = crear_nodo(nombre, duracion, series)
        if self.cabeza is None:
            nuevo["siguiente"] = nuevo["anterior"] = nuevo
            self.cabeza = self.actual = nuevo
        else:
            ultimo = self.cabeza["anterior"]
            ultimo["siguiente"] = nuevo
            nuevo["anterior"] = ultimo
            nuevo["siguiente"] = self.cabeza
            self.cabeza["anterior"] = nuevo
        self.tamano += 1

    def insertar_inicio(self, nombre, duracion, series):
        self.insertar_final(nombre, duracion, series)
        self.cabeza = self.cabeza["anterior"]

    def insertar_en(self, pos, nombre, duracion, series):
        if pos <= 0 or self.cabeza is None:
            return self.insertar_inicio(nombre, duracion, series)
        if pos >= self.tamano:
            return self.insertar_final(nombre, duracion, series)
        ref = self.cabeza
        for _ in range(pos):
            ref = ref["siguiente"]
        nuevo = crear_nodo(nombre, duracion, series)
        nuevo["anterior"], nuevo["siguiente"] = ref["anterior"], ref
        ref["anterior"]["siguiente"] = nuevo
        ref["anterior"] = nuevo
        self.tamano += 1

    def buscar(self, nombre):
        n = self.cabeza
        for _ in range(self.tamano):
            if n["nombre"].lower() == nombre.lower():
                return n
            n = n["siguiente"]
        return None

    def eliminar(self, nombre):
        nodo = self.buscar(nombre)
        if nodo is None:
            return False
        if self.tamano == 1:
            self.cabeza = self.actual = None
        else:
            nodo["anterior"]["siguiente"] = nodo["siguiente"]
            nodo["siguiente"]["anterior"] = nodo["anterior"]
            if nodo is self.cabeza:
                self.cabeza = nodo["siguiente"]
            if nodo is self.actual:
                self.actual = nodo["siguiente"]
        self.tamano -= 1
        return True

    def recorrer(self, reversa=False):
        res = []
        if self.cabeza is None:
            return res
        n = self.cabeza["anterior"] if reversa else self.cabeza
        for _ in range(self.tamano):
            res.append(n)
            n = n["anterior"] if reversa else n["siguiente"]
        return res


lista = ListaCircularDoble()
for e in [("Calentamiento", 20, 1), ("Sentadillas", 15, 3), ("Flexiones", 15, 3),
          ("Plancha", 20, 2), ("Estiramiento", 20, 1)]:
    lista.insertar_final(*e)


def estado(reversa=False):
    a = lista.actual
    d = lambda n: {"nombre": n["nombre"], "duracion": n["duracion"], "series": n["series"]}
    return {
        "ejercicios": [d(n) for n in lista.recorrer(reversa)],
        "actual": d(a) if a else None,
        "anterior": a["anterior"]["nombre"] if a else None,
        "siguiente": a["siguiente"]["nombre"] if a else None,
        "total": sum(n["duracion"] * n["series"] for n in lista.recorrer()),
    }


def ejecutar(d):
    acc = d.get("accion")
    if acc in ("inicio", "final", "posicion"):
        nombre = str(d.get("nombre", "")).strip()
        dur, ser = int(d["duracion"]), int(d["series"])
        if not nombre or dur <= 0 or ser <= 0:
            raise ValueError("Datos invalidos")
        if acc == "inicio":
            lista.insertar_inicio(nombre, dur, ser)
        elif acc == "final":
            lista.insertar_final(nombre, dur, ser)
        else:
            lista.insertar_en(int(d["pos"]), nombre, dur, ser)
    elif acc == "eliminar":
        lista.eliminar(d["nombre"])
    elif acc == "buscar":
        n = lista.buscar(d["nombre"])
        if n is None:
            raise ValueError("Ejercicio no encontrado")
        lista.actual = n
    elif acc == "siguiente" and lista.actual:
        lista.actual = lista.actual["siguiente"]
    elif acc == "anterior" and lista.actual:
        lista.actual = lista.actual["anterior"]
    elif acc == "reiniciar":
        lista.actual = lista.cabeza


# ----------------------------------------------------------------------
# FRONTEND (HTML + CSS + JS)
# ----------------------------------------------------------------------
HTML = r"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Rutina de Ejercicios - Lista Circular Doble</title>
<style>
:root{--azul:#232F6B;--mor:#8B2C8F;--nar:#FF7F50;--ver:#2E9E6B;--bg:#F4F7FB}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,Helvetica,Arial,sans-serif;background:var(--bg);color:var(--azul)}
.wrap{max-width:1000px;margin:0 auto;padding:20px}
.tag{display:inline-block;background:var(--nar);color:#fff;font-weight:700;padding:6px 12px;font-size:14px}
h1{margin:12px 0 18px;font-size:32px}h1 span{color:var(--mor)}
.grid{display:grid;grid-template-columns:1.3fr 1fr;gap:20px}
@media(max-width:800px){.grid{grid-template-columns:1fr}}
.card{background:#fff;border:1px solid #D8DFEC;border-radius:12px;padding:16px}
table{width:100%;border-collapse:collapse}
th,td{padding:8px;text-align:left;border-bottom:1px solid #eee}
th{font-size:13px;color:var(--mor)}
tr.act{background:#D9F2E6;font-weight:700}
tr{cursor:pointer}
.form{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 8px}
input{padding:8px;border:1px solid #C5CDE0;border-radius:6px;font-size:14px}
#nombre{flex:2;min-width:130px}#dur,#ser,#pos{width:80px}
button{padding:8px 12px;border:0;border-radius:6px;background:var(--azul);color:#fff;font-size:14px;cursor:pointer}
button:hover{opacity:.85}
button.sec{background:#E3E8F4;color:var(--azul)}button.ver{background:var(--ver)}button.rojo{background:#D64545}
.row{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px}
.panel{text-align:center}
.panel small{color:var(--mor);font-weight:700;letter-spacing:1px}
#ej{font-size:28px;font-weight:800;margin:8px 0}
#tiempo{font-size:72px;font-weight:800;color:var(--ver);line-height:1}
#serie{color:#666;margin:6px 0}
#vec{color:#666;font-size:14px;margin:12px 0}
#msg{color:#D64545;min-height:20px;font-size:14px}
</style></head>
<body><div class="wrap">
<h1>Rutina de Ejercicios</h1>
<div class="grid">
  <div class="card">
    <table><thead><tr><th>#</th><th>Ejercicio</th><th>Seg/serie</th><th>Series</th></tr></thead><tbody id="tabla"></tbody></table>
    <div class="form">
      <input id="nombre" placeholder="Nombre del ejercicio">
      <input id="dur" type="number" min="1" placeholder="Seg">
      <input id="ser" type="number" min="1" placeholder="Series">
      <input id="pos" type="number" min="0" placeholder="Pos.">
    </div>
    <div class="row">
      <button onclick="add('inicio')">Agregar al inicio</button>
      <button onclick="add('final')">Agregar al final</button>
      <button onclick="add('posicion')">Insertar en pos.</button>
    </div>
    <div class="row">
      <button class="sec" onclick="buscar()">Buscar</button>
      <button class="rojo" onclick="eliminar()">Eliminar seleccionado</button>
      <button class="sec" id="btnRev" onclick="sentido()">Ver: Adelante ▶</button>
    </div>
    <p id="msg"></p><p id="info"></p>
  </div>
  <div class="card panel">
    <small>EJERCICIO ACTUAL</small>
    <div id="ej">-</div><div id="serie"></div><div id="tiempo">00</div>
    <div id="vec"></div>
    <div class="row" style="justify-content:center">
      <button class="sec" onclick="mover('anterior')">◀ Anterior</button>
      <button class="sec" onclick="mover('siguiente')">Siguiente ▶</button>
    </div>
    <div class="row" style="justify-content:center">
      <button class="ver" onclick="iniciar()">▶ Iniciar</button>
      <button class="sec" onclick="detener()">■ Detener</button>
      <button class="sec" onclick="reiniciar()">↺ Reiniciar</button>
    </div>
  </div>
</div></div>
<script>
let S=null, reversa=false, sel=null, timer=null, rest=0, serieAct=1;
const $=id=>document.getElementById(id);
const esc=t=>String(t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

async function api(body){
  $('msg').textContent='';
  const r=await fetch('/api/accion',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...body,reversa})});
  const j=await r.json();
  if(j.error){$('msg').textContent=j.error;return false}
  S=j;pintar();return true;
}
function pintar(){
  $('tabla').innerHTML=S.ejercicios.map((e,i)=>
    `<tr class="${S.actual&&e.nombre===S.actual.nombre?'act':''}" onclick="sel='${esc(e.nombre).replace(/'/g,"\\'")}';$('nombre').value=sel">
     <td>${i+1}</td><td>${esc(e.nombre)}</td><td>${e.duracion}</td><td>${e.series}</td></tr>`).join('');
  const a=S.actual;
  $('ej').textContent=a?a.nombre:'Rutina vacía';
  $('serie').textContent=a?`Serie ${serieAct} de ${a.series} · ${a.duracion}s`:'';
  if(!timer)$('tiempo').textContent=a?String(a.duracion).padStart(2,'0'):'00';
  $('vec').textContent=a?`◀ ${S.anterior}   |   ${S.siguiente} ▶`:'';
  $('info').textContent=`Ejercicios: ${S.ejercicios.length} · Duración total: ${Math.floor(S.total/60)} min ${S.total%60} s`;
}
function add(acc){
  api({accion:acc,nombre:$('nombre').value,duracion:$('dur').value,series:$('ser').value,pos:$('pos').value||0})
   .then(ok=>{if(ok)['nombre','dur','ser','pos'].forEach(i=>$(i).value='')});
}
function eliminar(){const n=$('nombre').value.trim();if(!n){$('msg').textContent='Selecciona o escribe un ejercicio';return}detener();api({accion:'eliminar',nombre:n})}
function buscar(){detener();api({accion:'buscar',nombre:$('nombre').value})}
function sentido(){reversa=!reversa;$('btnRev').textContent=reversa?'Ver: Atrás ◀':'Ver: Adelante ▶';api({accion:'ver'})}
function mover(a){detener();serieAct=1;api({accion:a})}
function reiniciar(){detener();serieAct=1;api({accion:'reiniciar'})}
function detener(){if(timer){clearInterval(timer);timer=null}}
function iniciar(){
  if(timer||!S.actual)return;
  serieAct=1;rest=S.actual.duracion;
  timer=setInterval(async()=>{
    $('tiempo').textContent=String(rest).padStart(2,'0');
    $('serie').textContent=`Serie ${serieAct} de ${S.actual.series} · ${S.actual.duracion}s`;
    if(rest>0){rest--;return}
    if(serieAct<S.actual.series){serieAct++;rest=S.actual.duracion}
    else{serieAct=1;clearInterval(timer);timer=null;await api({accion:'siguiente'});iniciar()} // al final vuelve al primero
  },1000);
}
api({accion:'ver'});
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _enviar(self, codigo, contenido, tipo):
        datos = contenido.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        self._enviar(200, HTML, "text/html; charset=utf-8")

    def do_POST(self):
        largo = int(self.headers.get("Content-Length", 0))
        datos = json.loads(self.rfile.read(largo) or "{}")
        try:
            ejecutar(datos)
            resp = estado(bool(datos.get("reversa")))
        except Exception as ex:
            resp = {"error": str(ex)}
        self._enviar(200, json.dumps(resp), "application/json")

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    url = "http://localhost:8000"
    servidor = HTTPServer(("localhost", 8000), Handler)
    print(f"Servidor activo en {url}  (Ctrl+C para detener)")
    threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor detenido")

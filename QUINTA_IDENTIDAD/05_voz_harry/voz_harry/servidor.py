"""Interfaz local para generar, escuchar, guardar y comparar muestras. Solo biblioteca estándar.

- Escucha SOLO en 127.0.0.1 y rechaza peticiones con otra cabecera Host (protege
  contra el «DNS rebinding»). Los POST exigen JSON.
- No usa micrófono ni escucha permanente: solo reproduce audio generado.
- Se apaga con Ctrl-C; no instala ningún servicio persistente.
- Cada motor corre en su trabajador, con el modelo cargado mientras la interfaz
  está abierta. Al cerrar la interfaz se cierran los trabajadores.
"""

from __future__ import annotations

import csv
import json
import mimetypes
import shutil
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Tuple
from urllib.parse import unquote, urlparse

from . import catalogo, equipo, rutas
from .cliente import ClienteMotor, ErrorCliente, entorno_listo

ANFITRION = "127.0.0.1"
MAX_TEXTO = 2000
CAMPOS_VALORACION = ["fecha", "muestra", "codigo_a_ciegas", "naturalidad_1_5", "inteligibilidad_1_5", "edad_aparente",
                     "timbre", "calidez_1_5", "expresividad_1_5", "solemne_o_teatral", "acento", "notas"]


class Estado:
    def __init__(self):
        self.equipo = equipo.describir()
        self.clientes: Dict[Tuple[str, str], ClienteMotor] = {}
        self.candado = threading.Lock()

    def cliente(self, motor: str, opciones: Dict[str, Any]) -> ClienteMotor:
        clave = (motor, json.dumps(opciones, sort_keys=True))
        with self.candado:
            if clave not in self.clientes:
                self.clientes[clave] = ClienteMotor(motor, opciones)
            return self.clientes[clave]

    def cerrar(self):
        for c in self.clientes.values():
            c.cerrar()


def estado_motores() -> Dict[str, Any]:
    cat = catalogo.cargar()
    salida = {}
    for nombre, info in cat["motores"].items():
        salida[nombre] = {
            "nombre": info["nombre"], "entorno_listo": entorno_listo(nombre),
            "controles_nativos": info.get("controles_nativos", {}),
            "velocidad_nativa": nombre != "chatterbox",
            "estado_descarga": info.get("estado_descarga"), "licencia": info.get("licencia_codigo"),
            "marca_de_agua": info.get("marca_de_agua"),
        }
    return salida


def listar_muestras():
    salida = []
    for j in sorted(rutas.muestras().glob("**/*.json")):
        try:
            meta = json.loads(j.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if meta.get("formato") != "voz_harry/muestra 1":
            continue
        wav = j.with_suffix(".wav")
        if not wav.exists():
            continue
        rel = wav.relative_to(rutas.muestras()).as_posix()
        salida.append({
            "ruta": rel, "url": "/muestras/" + rel, "motor": meta["motor"], "voz": meta["voz"], "idioma": meta["idioma"],
            "prueba": ((meta.get("contexto") or {}).get("prueba")
                       or ("primera" if (meta.get("contexto") or {}).get("origen") == "primera muestra" else "interfaz")),
            "texto": meta["texto"],
            "equipo": meta["equipo"]["etiqueta"], "aviso_equipo": meta["equipo"].get("aviso"),
            "tiempos": meta["tiempos"], "memoria": meta["memoria"], "medidas": meta["medidas"],
            "controles_nativos": meta["controles_nativos"], "posproceso": meta["posproceso"], "fecha": meta["fecha"],
            "experimental": (meta.get("contexto") or {}).get("experimental", False),
            "prueba_de_tuberia": meta["motor"] in ("espeak_prueba", "seno_prueba"),
        })
    return salida


class Manejador(BaseHTTPRequestHandler):
    estado: Estado = None  # se asigna al crear el servidor
    server_version = "VozHarry/0.1"

    def log_message(self, formato, *args):
        pass

    # ------------------------------------------------------------ utilidades
    def _host_valido(self) -> bool:
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ("127.0.0.1", "localhost")

    def _json(self, datos, codigo=200):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def _archivo(self, ruta: Path, tipo: str = None):
        datos = ruta.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", tipo or mimetypes.guess_type(str(ruta))[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def _cuerpo(self) -> Dict[str, Any]:
        if "application/json" not in (self.headers.get("Content-Type") or ""):
            raise ValueError("Se espera Content-Type: application/json")
        n = int(self.headers.get("Content-Length") or 0)
        if n > 100_000:
            raise ValueError("Petición demasiado grande")
        return json.loads(self.rfile.read(n) or b"{}")

    # ------------------------------------------------------------------ GET
    def do_GET(self):
        if not self._host_valido():
            return self._json({"error": "Host no permitido"}, 403)
        ruta = unquote(urlparse(self.path).path)
        if ruta in ("/", "/index.html"):
            return self._archivo(rutas.raiz() / "interfaz" / "index.html", "text/html; charset=utf-8")
        if ruta == "/api/estado":
            cat = catalogo.cargar()
            return self._json({"equipo": self.estado.equipo, "motores": estado_motores(), "voces": cat["voces"],
                               "textos": catalogo.textos(), "ffmpeg": bool(shutil.which("ffmpeg")),
                               "referencias_autorizadas": cat.get("referencias_de_voz_autorizadas", [])})
        if ruta == "/api/muestras":
            return self._json({"muestras": listar_muestras()})
        if ruta.startswith("/muestras/"):
            base = rutas.muestras().resolve()
            destino = (base / ruta[len("/muestras/"):]).resolve()
            if base not in destino.parents or destino.suffix.lower() != ".wav" or not destino.exists():
                return self._json({"error": "no encontrado"}, 404)
            return self._archivo(destino, "audio/wav")
        return self._json({"error": "no encontrado"}, 404)

    # ----------------------------------------------------------------- POST
    def do_POST(self):
        if not self._host_valido():
            return self._json({"error": "Host no permitido"}, 403)
        ruta = urlparse(self.path).path
        try:
            p = self._cuerpo()
            if ruta == "/api/sintetizar":
                return self._json(self._sintetizar(p))
            if ruta == "/api/valorar":
                return self._json(self._valorar(p))
            return self._json({"error": "no encontrado"}, 404)
        except (ValueError, KeyError) as e:
            return self._json({"error": str(e)}, 400)
        except ErrorCliente as e:
            return self._json({"error": str(e)}, 502)

    def _sintetizar(self, p):
        cat = catalogo.cargar()
        motor, voz, idioma = p["motor"], p["voz"], p["idioma"]
        texto = str(p.get("texto", "")).strip()
        if motor not in cat["motores"]:
            raise ValueError(f"Motor desconocido: {motor}")
        if not texto or len(texto) > MAX_TEXTO:
            raise ValueError(f"El texto debe tener entre 1 y {MAX_TEXTO} caracteres")
        voces = [v for v in cat["voces"] if v["motor"] == motor and v["id"] == voz]
        if motor == "chatterbox" and voz != "predeterminada":
            if voz not in {r["id"] for r in cat.get("referencias_de_voz_autorizadas", [])}:
                raise ValueError("Esa voz de referencia no está autorizada")
        elif not voces:
            raise ValueError(f"La voz {voz} no está en el catálogo de {motor}")
        compatible = any(idioma in v["idiomas"] for v in voces) if voces else idioma in ("es", "en")
        if not compatible and not p.get("experimental"):
            raise ValueError(f"La voz {voz} no está prevista para el idioma {idioma}; márcalo como experimental para probarlo")
        variante = next((v for v in voces if idioma in v["idiomas"]), voces[0] if voces else {})
        nativos = {k: float(v) for k, v in (p.get("nativos") or {}).items() if isinstance(v, (int, float))}
        if variante.get("lang_code"):
            nativos["lang_code"] = variante["lang_code"]
        post = {"tono_semitonos": float(p.get("tono_semitonos", 0.0)), "tempo": 1.0}
        opciones = {k: p[k] for k in ("dispositivo", "variante") if p.get(k)}
        sello = datetime.now().strftime("%Y%m%d-%H%M%S")
        voz_archivo = catalogo.clave_voz({"id": voz})
        destino = (rutas.muestras() / self.estado.equipo["etiqueta"] / "interfaz" /
                   f"{sello}__{motor}__{voz_archivo}__{idioma}.wav")
        meta = self.estado.cliente(motor, opciones).sintetizar(
            texto=texto, voz=voz, idioma=idioma, velocidad=float(p.get("velocidad", 1.0)), nativos=nativos,
            posproceso=post, salida_wav=str(destino),
            contexto={"origen": "interfaz", "experimental": not compatible})
        rel = destino.relative_to(rutas.muestras()).as_posix()
        return {"url": "/muestras/" + rel, "ruta": rel, "metadatos": meta}

    def _valorar(self, p):
        base = rutas.muestras().resolve()
        destino = (base / str(p["muestra"])).resolve()
        if base not in destino.parents or not destino.exists():
            raise ValueError("Muestra desconocida")
        archivo = rutas.evaluacion() / "valoraciones.csv"
        archivo.parent.mkdir(parents=True, exist_ok=True)
        nuevo = not archivo.exists()
        fila = {c: str(p.get(c, ""))[:500] for c in CAMPOS_VALORACION}
        fila["fecha"] = datetime.now().isoformat(timespec="seconds")
        fila["muestra"] = destino.relative_to(base).as_posix()
        with open(archivo, "a", newline="", encoding="utf-8-sig" if nuevo else "utf-8") as f:
            w = csv.DictWriter(f, fieldnames=CAMPOS_VALORACION)
            if nuevo:
                w.writeheader()
            w.writerow(fila)
        return {"guardado": str(archivo.relative_to(rutas.raiz()))}


def servir(puerto: int = 8765, abrir: bool = False) -> None:
    estado = Estado()
    Manejador.estado = estado
    srv = ThreadingHTTPServer((ANFITRION, puerto), Manejador)
    url = f"http://{ANFITRION}:{srv.server_address[1]}/"
    print(f"Interfaz de voz en {url} (solo este equipo). Ctrl-C para cerrar.")
    print(f"Equipo: {estado.equipo['etiqueta']} · {estado.equipo['aviso']}")
    if abrir:
        import webbrowser
        webbrowser.open(url)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
        estado.cerrar()
        print("Interfaz cerrada; trabajadores detenidos.")

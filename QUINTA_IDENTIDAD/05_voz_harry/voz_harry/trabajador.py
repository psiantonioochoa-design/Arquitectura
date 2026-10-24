"""Trabajador de un motor: corre DENTRO del entorno aislado de ese motor.

Uso (lo lanza cliente.py):  entornos/<motor>/bin/python -I voz_harry/trabajador.py --motor <motor>

Protocolo: una petición JSON por línea en stdin y una respuesta JSON por línea en
stdout. El modelo queda cargado entre peticiones mientras el proceso vive; el
proceso termina con {"orden": "salir"} o al cerrarse stdin. No escucha en la red.

  {"orden": "describir"}
  {"orden": "sintetizar", "texto": "...", "voz": "...", "idioma": "es", "velocidad": 1.0,
   "nativos": {...}, "posproceso": {"tono_semitonos": 0, "tempo": 1.0},
   "salida_wav": "/ruta/x.wav", "contexto": {...}}
"""

from __future__ import annotations

import hashlib
import json
import os
import resource
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from voz_harry import VERSION, equipo  # noqa: E402
from voz_harry.audio import escribir_wav, medidas  # noqa: E402
from voz_harry.motores import ErrorMotor, crear  # noqa: E402
from voz_harry.postproceso import aplicar  # noqa: E402


def _rss_max_mb() -> float:
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return round(r / 2**20 if sys.platform == "darwin" else r / 1024, 1)  # macOS: bytes; Linux: KiB


def _rss_actual_mb():
    try:
        with open("/proc/self/status", encoding="utf-8") as f:
            for linea in f:
                if linea.startswith("VmRSS:"):
                    return round(int(linea.split()[1]) / 1024, 1)
    except OSError:
        return None  # en macOS lo mide el cliente con ps
    return None


def _memoria_gpu_mb():
    try:
        import torch
        if torch.backends.mps.is_available():
            return {"mps_asignada_mb": round(torch.mps.current_allocated_memory() / 2**20, 1),
                    "mps_driver_mb": round(torch.mps.driver_allocated_memory() / 2**20, 1)}
        if torch.cuda.is_available():
            return {"cuda_pico_mb": round(torch.cuda.max_memory_allocated() / 2**20, 1)}
    except Exception:
        pass
    return {}


def _sha256(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


class Trabajador:
    def __init__(self, motor: str, opciones):
        self.nombre = motor
        inicio = time.monotonic()
        self.motor = crear(motor, opciones)
        self.carga_inicial_s = round(time.monotonic() - inicio, 3)
        self.primera_por_voz = set()
        self.equipo = equipo.describir()

    def describir(self):
        d = self.motor.describir()
        d.update({"equipo": self.equipo, "rss_max_mb": _rss_max_mb(), "sin_conexion_hf": os.environ.get("HF_HUB_OFFLINE") == "1"})
        return d

    def sintetizar(self, p):
        texto, voz, idioma = p["texto"], p["voz"], p["idioma"]
        velocidad = float(p.get("velocidad", 1.0))
        nativos = dict(p.get("nativos") or {})
        post = dict(p.get("posproceso") or {})
        tempo_post = float(post.get("tempo", 1.0))
        velocidad_nativa = velocidad
        if not self.motor.velocidad_nativa and abs(velocidad - 1.0) > 1e-6:
            tempo_post *= velocidad  # el motor no tiene velocidad nativa: se aplica después y se declara
            velocidad_nativa = 1.0
        clave = (voz, idioma)
        primera = clave not in self.primera_por_voz
        inicio = time.monotonic()
        audio, sr, aplicados = self.motor.sintetizar(texto, voz, idioma, velocidad_nativa, nativos)
        sintesis_s = time.monotonic() - inicio
        self.primera_por_voz.add(clave)
        audio, desc_post = aplicar(audio, sr, float(post.get("tono_semitonos", 0.0)), tempo_post)
        if desc_post and not self.motor.velocidad_nativa and abs(velocidad - 1.0) > 1e-6:
            desc_post["nota"] = "la velocidad pedida se aplicó como posproceso porque el motor no la tiene nativa"
        salida = Path(p["salida_wav"])
        salida.parent.mkdir(parents=True, exist_ok=True)
        escribir_wav(salida, audio, sr)
        m = medidas(audio, sr, texto)
        meta = {
            "formato": "voz_harry/muestra 1",
            "archivo": salida.name,
            "sha256_wav": _sha256(salida),
            "fecha": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            "motor": self.nombre,
            "motor_detalle": self.motor.describir(),
            "voz": voz,
            "idioma": idioma,
            "texto": texto,
            "contexto": p.get("contexto") or {},
            "velocidad_pedida": velocidad,
            "controles_nativos": aplicados,
            "posproceso": desc_post or "ninguno",
            "tiempos": {
                "carga_motor_s": self.carga_inicial_s,
                "sintesis_s": round(sintesis_s, 3),
                "incluye_carga_de_voz": primera,
                "factor_tiempo_real": round(sintesis_s / m["duracion_s"], 3) if m["duracion_s"] else None,
            },
            "memoria": {"rss_max_proceso_mb": _rss_max_mb(), "rss_actual_mb": _rss_actual_mb(), **_memoria_gpu_mb(),
                        "nota": "rss_max es el pico del proceso desde que arrancó (incluye cargar el modelo)"},
            "medidas": m,
            "equipo": self.equipo,
            "sin_conexion_hf": os.environ.get("HF_HUB_OFFLINE") == "1",
            "version_voz_harry": VERSION,
            "aviso": ("Muestra de comparación acústica. El texto no es una respuesta aprobada de Harry. "
                      "Las medidas son objetivas; la valoración auditiva la hace el custodio."),
        }
        salida.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return meta


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--motor", required=True)
    ap.add_argument("--opciones", default="{}", help="JSON con opciones del motor (dispositivo, variante…)")
    args = ap.parse_args()
    salida = sys.stdout
    sys.stdout = sys.stderr  # cualquier print de las bibliotecas va al registro, no al protocolo
    try:
        t = Trabajador(args.motor, json.loads(args.opciones))
        salida.write(json.dumps({"ok": True, "listo": True, "carga_motor_s": t.carga_inicial_s}) + "\n")
        salida.flush()
    except Exception as e:
        salida.write(json.dumps({"ok": False, "listo": False, "error": f"{type(e).__name__}: {e}"}) + "\n")
        salida.flush()
        return 1
    for linea in sys.stdin:
        if not linea.strip():
            continue
        p = json.loads(linea)
        try:
            if p.get("orden") == "salir":
                break
            if p.get("orden") == "describir":
                r = {"ok": True, "datos": t.describir()}
            elif p.get("orden") == "sintetizar":
                r = {"ok": True, "datos": t.sintetizar(p)}
            else:
                r = {"ok": False, "error": f"orden desconocida: {p.get('orden')}"}
        except ErrorMotor as e:
            r = {"ok": False, "error": str(e)}
        except Exception as e:
            traceback.print_exc()
            r = {"ok": False, "error": f"{type(e).__name__}: {e}"}
        r["id"] = p.get("id")
        salida.write(json.dumps(r, ensure_ascii=False) + "\n")
        salida.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

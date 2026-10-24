"""Lado del orquestador: lanza y habla con el trabajador de cada motor. Solo biblioteca estándar.

El trabajador corre con el Python del entorno aislado del motor
(entornos/<motor>/bin/python) y en modo sin conexión (HF_HUB_OFFLINE=1): si un
peso no está en la caché del proyecto, falla en lugar de descargarlo.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Optional

from . import rutas


class ErrorCliente(Exception):
    pass


def entorno_listo(motor: str) -> bool:
    return rutas.python_de(motor).exists()


class ClienteMotor:
    def __init__(self, motor: str, opciones: Optional[Dict[str, Any]] = None, python: Optional[str] = None,
                 tiempo_espera_s: float = 900.0):
        self.motor = motor
        self.opciones = opciones or {}
        self.python = python or str(rutas.python_de(motor))
        self.tiempo_espera_s = tiempo_espera_s
        self.proc: Optional[subprocess.Popen] = None
        self._n = 0
        self._candado = threading.Lock()
        self.registro = rutas.evaluacion() / "registros" / f"trabajador_{motor}.log"

    def iniciar(self) -> Dict[str, Any]:
        if not Path(self.python).exists():
            raise ErrorCliente(f"No existe el entorno de {self.motor} ({self.python}). Crea el entorno con "
                               f"instalar/crear_entornos.sh {self.motor}")
        env = dict(os.environ)
        env.setdefault("HF_HOME", str(rutas.cache_hf()))
        env.setdefault("HF_HUB_OFFLINE", "1")
        env.setdefault("TRANSFORMERS_OFFLINE", env["HF_HUB_OFFLINE"])
        env["TOKENIZERS_PARALLELISM"] = "false"
        env["VOZ_RAIZ"] = str(rutas.raiz())
        if self.opciones.get("dispositivo") == "mps":
            env["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
        self.registro.parent.mkdir(parents=True, exist_ok=True)
        self._log = open(self.registro, "a", encoding="utf-8")
        self.proc = subprocess.Popen(
            [self.python, "-I", str(rutas.raiz() / "voz_harry" / "trabajador.py"), "--motor", self.motor,
             "--opciones", json.dumps(self.opciones)],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self._log, text=True, encoding="utf-8", env=env,
        )
        listo = self._leer()
        if not listo.get("ok"):
            self.cerrar()
            raise ErrorCliente(f"El trabajador de {self.motor} no arrancó: {listo.get('error')} (ver {self.registro})")
        return listo

    def _leer(self) -> Dict[str, Any]:
        resultado: Dict[str, Any] = {}

        def leer():
            linea = self.proc.stdout.readline()
            resultado["linea"] = linea

        hilo = threading.Thread(target=leer, daemon=True)
        hilo.start()
        hilo.join(self.tiempo_espera_s)
        if hilo.is_alive():
            self.cerrar()
            raise ErrorCliente(f"El trabajador de {self.motor} no respondió en {self.tiempo_espera_s} s")
        if not resultado.get("linea"):
            raise ErrorCliente(f"El trabajador de {self.motor} terminó (ver {self.registro})")
        return json.loads(resultado["linea"])

    def pedir(self, orden: Dict[str, Any]) -> Dict[str, Any]:
        with self._candado:
            if self.proc is None or self.proc.poll() is not None:
                self.iniciar()
            self._n += 1
            orden = dict(orden, id=self._n)
            self.proc.stdin.write(json.dumps(orden, ensure_ascii=False) + "\n")
            self.proc.stdin.flush()
            r = self._leer()
        if not r.get("ok"):
            raise ErrorCliente(r.get("error", "error desconocido"))
        datos = r["datos"]
        if sys.platform == "darwin" and isinstance(datos, dict) and "memoria" in datos:
            datos["memoria"]["rss_actual_mb"] = self.rss_actual_mb()
        return datos

    def rss_actual_mb(self) -> Optional[float]:
        if self.proc is None:
            return None
        try:
            kb = subprocess.run(["ps", "-o", "rss=", "-p", str(self.proc.pid)], capture_output=True, text=True).stdout.strip()
            return round(int(kb) / 1024, 1) if kb else None
        except Exception:
            return None

    def describir(self) -> Dict[str, Any]:
        return self.pedir({"orden": "describir"})

    def sintetizar(self, **peticion) -> Dict[str, Any]:
        return self.pedir(dict(peticion, orden="sintetizar"))

    def cerrar(self) -> None:
        if self.proc is not None:
            try:
                if self.proc.poll() is None:
                    self.proc.stdin.write(json.dumps({"orden": "salir"}) + "\n")
                    self.proc.stdin.flush()
                    self.proc.wait(timeout=10)
            except Exception:
                self.proc.kill()
            for flujo in (self.proc.stdin, self.proc.stdout):
                try:
                    flujo.close()
                except Exception:
                    pass
            self.proc = None
        if getattr(self, "_log", None):
            self._log.close()
            self._log = None

    def __enter__(self):
        self.iniciar()
        return self

    def __exit__(self, *_):
        self.cerrar()

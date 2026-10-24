"""Rutas de 05_voz_harry. Todo vive dentro de esta carpeta, salvo que se indique otra.

  entornos/<motor>/   entorno de Python aislado de cada motor (no se versiona)
  modelos/            pesos descargados; modelos/hf es la caché de Hugging Face del
                      proyecto (no se versiona; se puede apuntar a una caché existente
                      con VOZ_MODELOS o HF_HOME para no copiar pesos)
  muestras/<equipo>/  WAV y metadatos, separados por el equipo que los generó
  evaluacion/         hojas de escucha del custodio
"""

from __future__ import annotations

import os
from pathlib import Path


def raiz() -> Path:
    env = os.environ.get("VOZ_RAIZ")
    return Path(env).expanduser().resolve() if env else Path(__file__).resolve().parents[1]


def configuracion() -> Path:
    return raiz() / "configuracion"


def entornos() -> Path:
    return Path(os.environ.get("VOZ_ENTORNOS", raiz() / "entornos")).expanduser()


def modelos() -> Path:
    return Path(os.environ.get("VOZ_MODELOS", raiz() / "modelos")).expanduser()


def cache_hf() -> Path:
    """Caché de Hugging Face del proyecto, salvo que HF_HOME ya apunte a otra."""
    return Path(os.environ.get("HF_HOME", modelos() / "hf")).expanduser()


def muestras() -> Path:
    return raiz() / "muestras"


def evaluacion() -> Path:
    return raiz() / "evaluacion"


def python_de(motor: str) -> Path:
    base = entornos() / motor
    for candidato in (base / "bin" / "python", base / "Scripts" / "python.exe"):
        if candidato.exists():
            return candidato
    return base / "bin" / "python"

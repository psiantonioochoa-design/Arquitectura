"""Rutas del proyecto. Todo se resuelve a partir de la raíz de QUINTA_IDENTIDAD.

La raíz se deduce de la ubicación de este archivo, o se fija con la variable de
entorno QUINTA_RAIZ (útil si el SSD se monta con otro nombre).
"""

from __future__ import annotations

import os
from pathlib import Path


def raiz() -> Path:
    env = os.environ.get("QUINTA_RAIZ")
    if env:
        return Path(env).expanduser().resolve()
    # codigo/harry_nucleo/rutas.py -> harry_nucleo -> codigo -> 06_implementacion -> raíz
    return Path(__file__).resolve().parents[3]


def impl() -> Path:
    return raiz() / "06_implementacion"


def evaluaciones() -> Path:
    return raiz() / "07_evaluaciones"


def expandir(texto: str) -> str:
    """Sustituye ${RAIZ}, ${IMPL} y ${EVAL} en una ruta de configuración."""
    return (
        texto.replace("${RAIZ}", str(raiz()))
        .replace("${IMPL}", str(impl()))
        .replace("${EVAL}", str(evaluaciones()))
    )


def ruta(texto: str) -> Path:
    return Path(expandir(texto)).expanduser()

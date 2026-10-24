"""Carga y valida la configuración del proyecto y de cada plataforma."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from . import rutas
from .util import leer_json


class ErrorConfiguracion(Exception):
    pass


def cargar_proyecto() -> Dict[str, Any]:
    p = rutas.impl() / "configuracion" / "proyecto.json"
    if not p.exists():
        raise ErrorConfiguracion(f"No existe {p}")
    datos = leer_json(p)
    for clave in ("documentos_vigilados", "casos_ejecutables", "carpetas_corridas", "aprobaciones", "conformidad"):
        if clave not in datos:
            raise ErrorConfiguracion(f"Falta '{clave}' en {p}")
    return datos


def ruta_plataforma(nombre_o_ruta: str) -> Path:
    """Acepta un nombre ('simulacion') o la ruta a un .json."""
    candidato = Path(nombre_o_ruta).expanduser()
    if candidato.suffix == ".json" and candidato.exists():
        return candidato.resolve()
    p = rutas.impl() / "configuracion" / "plataformas" / f"{nombre_o_ruta}.json"
    if not p.exists():
        disponibles = sorted(x.stem for x in p.parent.glob("*.json"))
        raise ErrorConfiguracion(
            f"No encuentro la plataforma '{nombre_o_ruta}'. Disponibles: {', '.join(disponibles)}"
        )
    return p


def cargar_plataforma(nombre_o_ruta: str) -> Dict[str, Any]:
    p = ruta_plataforma(nombre_o_ruta)
    datos = leer_json(p)
    datos["_ruta_config"] = str(p)
    for clave in ("id", "adaptador", "instrucciones", "capacidades"):
        if clave not in datos:
            raise ErrorConfiguracion(f"Falta '{clave}' en {p}")
    tipo = datos["adaptador"].get("tipo")
    if tipo not in ("simulacion", "ollama"):
        raise ErrorConfiguracion(f"Tipo de adaptador desconocido en {p}: {tipo!r}")
    if tipo == "ollama":
        for clave in ("host", "modelo"):
            if not datos["adaptador"].get(clave):
                raise ErrorConfiguracion(f"Falta adaptador.{clave} en {p}")
    return datos

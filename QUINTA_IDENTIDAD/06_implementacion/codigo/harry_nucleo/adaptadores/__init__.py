from __future__ import annotations

from typing import Any, Dict

from .base import Adaptador, ErrorAdaptador, Resultado


def crear(plataforma: Dict[str, Any]) -> Adaptador:
    cfg = plataforma["adaptador"]
    if cfg["tipo"] == "simulacion":
        from .simulacion import AdaptadorSimulacion
        return AdaptadorSimulacion(cfg)
    if cfg["tipo"] == "ollama":
        from .ollama import AdaptadorOllama
        return AdaptadorOllama(cfg)
    raise ValueError(f"Adaptador desconocido: {cfg['tipo']}")


__all__ = ["Adaptador", "ErrorAdaptador", "Resultado", "crear"]

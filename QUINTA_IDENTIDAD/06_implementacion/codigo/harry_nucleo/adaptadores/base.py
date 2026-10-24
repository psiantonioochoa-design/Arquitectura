"""Interfaz común de los adaptadores de modelo."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Resultado:
    texto: str
    estado: str  # 'completa' o 'incompleta'
    duracion_s: float
    primer_token_s: Optional[float] = None
    metricas: Dict[str, Any] = field(default_factory=dict)
    simulada: bool = False
    nota: str = ""


class ErrorAdaptador(Exception):
    """Error identificable. `reintentable` indica si tiene sentido repetir la unidad."""

    def __init__(self, tipo: str, mensaje: str, reintentable: bool):
        super().__init__(f"{tipo}: {mensaje}")
        self.tipo = tipo
        self.mensaje = mensaje
        self.reintentable = reintentable


class Adaptador:
    tipo = "base"

    def info(self) -> Dict[str, Any]:
        raise NotImplementedError

    def preparar(self) -> Dict[str, Any]:
        """Comprobaciones antes de una corrida. No debe cargar modelos."""
        return {}

    def responder(self, mensajes: List[Dict[str, str]], contexto: Dict[str, Any]) -> Resultado:
        raise NotImplementedError

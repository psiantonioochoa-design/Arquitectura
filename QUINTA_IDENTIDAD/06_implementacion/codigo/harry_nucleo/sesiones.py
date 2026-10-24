"""Historial por sesión. Sin memoria personal persistente.

Cada sesión guarda solo sus propios turnos, en memoria del proceso. Nada se
escribe a disco ni pasa de una sesión a otra. Al cerrarla, sus turnos se
descartan. (Las corridas de evaluación registran lo enviado en su carpeta de
resultados; eso es un registro técnico de conversaciones sintéticas, no
memoria de Harry.)
"""

from __future__ import annotations

import uuid
from typing import Dict, List

from .util import ahora_iso


class ErrorSesion(Exception):
    pass


class Sesion:
    def __init__(self) -> None:
        self.id = uuid.uuid4().hex
        self.creada = ahora_iso()
        self._turnos: List[Dict[str, object]] = []
        self.cerrada = False

    def _comprobar(self) -> None:
        if self.cerrada:
            raise ErrorSesion("La sesión está cerrada")

    def agregar_usuario(self, texto: str) -> None:
        self._comprobar()
        self._turnos.append({"rol": "usuario", "texto": texto, "fabricado": False})

    def agregar_harry(self, texto: str, fabricado: bool = False) -> None:
        self._comprobar()
        if not self._turnos:
            raise ErrorSesion("Una sesión no puede empezar con una respuesta de Harry")
        self._turnos.append({"rol": "harry", "texto": texto, "fabricado": fabricado})

    def historial(self) -> List[Dict[str, str]]:
        """Copia: modificarla no altera la sesión."""
        return [{"rol": t["rol"], "texto": t["texto"]} for t in self._turnos]

    def cerrar(self) -> None:
        self._turnos.clear()
        self.cerrada = True


class GestorSesiones:
    """Sesiones vivas en memoria. No persiste nada."""

    def __init__(self) -> None:
        self._sesiones: Dict[str, Sesion] = {}

    def nueva(self) -> Sesion:
        s = Sesion()
        self._sesiones[s.id] = s
        return s

    def obtener(self, sesion_id: str) -> Sesion:
        if sesion_id not in self._sesiones:
            raise ErrorSesion(f"No existe la sesión {sesion_id}")
        return self._sesiones[sesion_id]

    def cerrar(self, sesion_id: str) -> None:
        self.obtener(sesion_id).cerrar()
        del self._sesiones[sesion_id]

    def activas(self) -> int:
        return len(self._sesiones)

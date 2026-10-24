"""Interfaz común de los motores de voz. Cada motor corre en su propio entorno aislado."""

from __future__ import annotations

from typing import Any, Dict, Tuple


class ErrorMotor(Exception):
    pass


class Motor:
    nombre = "base"
    velocidad_nativa = True  # si no, la velocidad se aplica como posproceso y así se declara

    def __init__(self, opciones: Dict[str, Any]):
        self.opciones = opciones or {}

    def describir(self) -> Dict[str, Any]:
        """Versión, dispositivo y voces presentes en disco. No descarga nada."""
        raise NotImplementedError

    def sintetizar(self, texto: str, voz: str, idioma: str, velocidad: float,
                   nativos: Dict[str, Any]) -> Tuple[Any, int, Dict[str, Any]]:
        """Devuelve (audio float32 en [-1, 1], frecuencia de muestreo, controles nativos aplicados)."""
        raise NotImplementedError


def crear(nombre: str, opciones: Dict[str, Any]) -> Motor:
    if nombre == "piper":
        from .piper_motor import MotorPiper
        return MotorPiper(opciones)
    if nombre == "kokoro":
        from .kokoro_motor import MotorKokoro
        return MotorKokoro(opciones)
    if nombre == "chatterbox":
        from .chatterbox_motor import MotorChatterbox
        return MotorChatterbox(opciones)
    if nombre == "espeak_prueba":
        from .espeak_prueba import MotorEspeakPrueba
        return MotorEspeakPrueba(opciones)
    if nombre == "seno_prueba":
        from .seno_prueba import MotorSenoPrueba
        return MotorSenoPrueba(opciones)
    raise ErrorMotor(f"Motor desconocido: {nombre}")

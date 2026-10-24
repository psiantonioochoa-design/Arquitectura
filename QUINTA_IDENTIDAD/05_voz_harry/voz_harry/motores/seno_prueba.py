"""Motor de PRUEBA para las pruebas automáticas: genera tonos, no voz. Solo necesita numpy."""

from __future__ import annotations

import numpy as np

from .base import Motor


class MotorSenoPrueba(Motor):
    nombre = "seno_prueba"

    def describir(self):
        return {"motor": self.nombre, "version": "prueba", "aviso": "genera tonos; no es una voz"}

    def sintetizar(self, texto, voz, idioma, velocidad, nativos):
        sr = 16000
        f0 = float(nativos.get("f0", 110.0))
        dur = max(0.3, 0.06 * len(texto.split()) / float(velocidad or 1.0))
        t = np.arange(int(sr * dur)) / sr
        audio = 0.3 * np.sin(2 * np.pi * f0 * t) + 0.1 * np.sin(2 * np.pi * 2 * f0 * t)
        return audio.astype(np.float32), sr, {"f0": f0, "velocidad": float(velocidad or 1.0)}

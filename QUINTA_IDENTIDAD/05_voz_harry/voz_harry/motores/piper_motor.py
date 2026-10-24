"""Piper (piper-tts 1.8, OHF-Voice/piper1-gpl). Voces ONNX en modelos/piper/; CPU con onnxruntime.

Controles nativos: velocidad (length_scale = defecto de la voz ÷ velocidad),
noise_scale, noise_w_scale y speaker_id (voces de varios hablantes).
"""

from __future__ import annotations

from typing import Any, Dict, Tuple

import numpy as np

from .. import rutas
from .base import ErrorMotor, Motor


class MotorPiper(Motor):
    nombre = "piper"

    def __init__(self, opciones):
        super().__init__(opciones)
        self._voces: Dict[str, Any] = {}
        self.carpeta = rutas.modelos() / "piper"

    def describir(self):
        import piper  # noqa: F401
        from importlib.metadata import version
        presentes = sorted(p.name[:-5] for p in self.carpeta.glob("*.onnx")) if self.carpeta.exists() else []
        return {"motor": self.nombre, "version": version("piper-tts"), "dispositivo": "cpu (onnxruntime)",
                "voces_presentes": presentes, "carpeta_modelos": str(self.carpeta)}

    def _voz(self, voz: str):
        if voz not in self._voces:
            from piper import PiperVoice
            modelo = self.carpeta / f"{voz}.onnx"
            if not modelo.exists() or not (self.carpeta / f"{voz}.onnx.json").exists():
                raise ErrorMotor(f"La voz {voz} no está descargada en {self.carpeta}. "
                                 f"Orden: python3 instalar/descargar_modelos.py --motor piper --voz {voz} --autorizo")
            self._voces[voz] = PiperVoice.load(modelo)
        return self._voces[voz]

    def sintetizar(self, texto, voz, idioma, velocidad, nativos) -> Tuple[Any, int, Dict[str, Any]]:
        from piper import SynthesisConfig
        v = self._voz(voz)
        cfg = v.config
        base = float(getattr(cfg, "length_scale", 1.0) or 1.0)
        hablante = nativos.get("speaker_id")
        if isinstance(hablante, str) and not hablante.isdigit():
            mapa = getattr(cfg, "speaker_id_map", {}) or {}
            if hablante not in mapa:
                raise ErrorMotor(f"Hablante {hablante!r} no existe en {voz}. Disponibles: {sorted(mapa)[:20]}")
            hablante = mapa[hablante]
        aplicados = {
            "length_scale": round(base / float(velocidad or 1.0), 4),
            "noise_scale": nativos.get("noise_scale", getattr(cfg, "noise_scale", None)),
            "noise_w_scale": nativos.get("noise_w_scale", getattr(cfg, "noise_w_scale", None)),
            "speaker_id": int(hablante) if hablante is not None else None,
        }
        syn = SynthesisConfig(**{k: v for k, v in aplicados.items() if v is not None})
        trozos = [c.audio_float_array for c in v.synthesize(texto, syn_config=syn)]
        if not trozos:
            raise ErrorMotor("Piper no devolvió audio")
        return np.concatenate(trozos).astype(np.float32), int(cfg.sample_rate), aplicados

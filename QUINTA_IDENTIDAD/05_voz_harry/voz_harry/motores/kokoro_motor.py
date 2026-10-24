"""Kokoro-82M (kokoro 0.9.4, hexgrad). Pesos y voces en la caché de Hugging Face del proyecto.

Controles nativos: velocidad (speed) y mezcla de voces ('bm_george,bm_fable'
promedia sus estilos). lang_code: 'b' inglés británico, 'e' español (eSpeak NG).
Dispositivo: cpu por defecto; 'mps' exige PYTORCH_ENABLE_MPS_FALLBACK=1 (lo pone
el cliente) y queda por medir en el M4.
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np

from .base import ErrorMotor, Motor

REPO = "hexgrad/Kokoro-82M"
LANG = {"en": "b", "es": "e"}


class MotorKokoro(Motor):
    nombre = "kokoro"

    def __init__(self, opciones):
        super().__init__(opciones)
        self._tuberias: Dict[str, Any] = {}
        self.dispositivo = opciones.get("dispositivo", "cpu")

    def describir(self):
        from importlib.metadata import version
        return {"motor": self.nombre, "version": version("kokoro"), "misaki": version("misaki"),
                "dispositivo_pedido": self.dispositivo, "repo": REPO}

    def _tuberia(self, lang_code: str):
        if lang_code not in self._tuberias:
            from kokoro import KPipeline
            try:
                self._tuberias[lang_code] = KPipeline(lang_code=lang_code, repo_id=REPO, device=self.dispositivo)
            except Exception as e:  # sin conexión y sin caché, o MPS no disponible
                raise ErrorMotor(f"No se pudo cargar Kokoro ({lang_code}, {self.dispositivo}): {e}. "
                                 "¿Están descargados los pesos? python3 instalar/descargar_modelos.py --motor kokoro --autorizo")
        return self._tuberias[lang_code]

    def sintetizar(self, texto, voz, idioma, velocidad, nativos):
        lang_code = nativos.get("lang_code") or LANG.get(idioma)
        if not lang_code:
            raise ErrorMotor(f"Idioma no previsto para Kokoro: {idioma}")
        t = self._tuberia(lang_code)
        partes = []
        for _, _, audio in t(texto, voice=voz, speed=float(velocidad or 1.0), split_pattern=r"\n+"):
            if audio is not None:
                partes.append(audio.detach().cpu().numpy() if hasattr(audio, "detach") else np.asarray(audio))
        if not partes:
            raise ErrorMotor("Kokoro no devolvió audio")
        dispositivo = str(getattr(getattr(t, "model", None), "device", self.dispositivo))
        return (np.concatenate(partes).astype(np.float32), 24000,
                {"speed": float(velocidad or 1.0), "voice": voz, "lang_code": lang_code, "dispositivo": dispositivo})

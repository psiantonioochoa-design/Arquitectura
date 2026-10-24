"""Chatterbox Multilingual (Resemble AI). Solo con autorización expresa para descargar sus pesos.

- chatterbox-tts 0.1.7 de PyPI trae Multilingual V2; la V3 solo está en el código
  de GitHub, cuyo from_pretrained acepta t3_model='v3'. Se detecta por la firma.
- Sin una grabación de referencia autorizada se usa la voz incluida (conds.pt).
  Este adaptador se niega a usar una referencia que no figure en
  configuracion/catalogo.json → referencias_de_voz_autorizadas.
- Controles nativos: exaggeration, cfg_weight y temperature. La velocidad no es
  nativa: el trabajador la aplica como posproceso y así lo declara.
- Todo audio generado lleva la marca de agua Perth de Resemble AI.
"""

from __future__ import annotations

import inspect
import json
from typing import Any, Dict

from .. import rutas
from .base import ErrorMotor, Motor


class MotorChatterbox(Motor):
    nombre = "chatterbox"
    velocidad_nativa = False

    def __init__(self, opciones):
        super().__init__(opciones)
        self.dispositivo = opciones.get("dispositivo", "cpu")
        self.variante = opciones.get("variante", "v2")
        self._modelo = None

    def describir(self):
        from importlib.metadata import version
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        v3 = "t3_model" in inspect.signature(ChatterboxMultilingualTTS.from_pretrained).parameters
        return {"motor": self.nombre, "version": version("chatterbox-tts"), "admite_v3": v3,
                "variante_pedida": self.variante, "dispositivo_pedido": self.dispositivo,
                "marca_de_agua": "Perth (Resemble AI), siempre"}

    def _cargar(self):
        if self._modelo is None:
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            kwargs = {"device": self.dispositivo}
            if "t3_model" in inspect.signature(ChatterboxMultilingualTTS.from_pretrained).parameters:
                kwargs["t3_model"] = self.variante
            elif self.variante != "v2":
                raise ErrorMotor(f"Esta versión de chatterbox-tts solo trae Multilingual V2; pediste {self.variante}.")
            try:
                self._modelo = ChatterboxMultilingualTTS.from_pretrained(**kwargs)
            except Exception as e:
                raise ErrorMotor(f"No se pudo cargar Chatterbox ({kwargs}): {e}. La descarga de sus pesos exige "
                                 "autorización: python3 instalar/descargar_modelos.py --motor chatterbox --autorizo --autorizo-grande")
        return self._modelo

    def sintetizar(self, texto, voz, idioma, velocidad, nativos):
        referencia = None
        if voz not in ("predeterminada", "", None):
            catalogo = json.loads((rutas.configuracion() / "catalogo.json").read_text(encoding="utf-8"))
            autorizadas = {r["id"]: r for r in catalogo.get("referencias_de_voz_autorizadas", [])}
            if voz not in autorizadas:
                raise ErrorMotor(f"La voz de referencia {voz!r} no está autorizada en el catálogo. "
                                 "Solo se usan grabaciones con consentimiento expreso.")
            referencia = str(rutas.raiz() / autorizadas[voz]["archivo"])
        m = self._cargar()
        aplicados = {k: float(nativos.get(k, d)) for k, d in (("exaggeration", 0.5), ("cfg_weight", 0.5), ("temperature", 0.8))}
        wav = m.generate(texto, language_id=idioma, audio_prompt_path=referencia, **aplicados)
        audio = wav.squeeze(0).detach().cpu().numpy() if hasattr(wav, "detach") else wav
        aplicados.update({"variante": self.variante, "referencia": voz if referencia else "voz incluida (conds.pt)",
                          "dispositivo": self.dispositivo, "marca_de_agua": "Perth"})
        return audio.astype("float32"), int(m.sr), aplicados

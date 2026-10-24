"""eSpeak NG como motor de PRUEBA de la tubería. No es candidato para la voz de Harry.

Sirve para comprobar de punta a punta (síntesis, WAV, metadatos, medidas,
interfaz) donde los modelos neuronales no están disponibles, por ejemplo en
una sesión en la nube sin acceso a Hugging Face. Es una voz de formantes,
robótica. Usa la biblioteca que trae el paquete espeakng-loader (PyPI), sin
instalar nada en el sistema.

Voces: 'es-419+m3' (español latinoamericano, variante masculina 3) o
'gmw/en-GB-x-rp+m3' (inglés británico RP). Controles nativos: velocidad (rate = 175 × velocidad, en palabras
por minuto) y tono (pitch, 0–100).
"""

from __future__ import annotations

import ctypes
import os
import tempfile
from typing import Any, Dict, List

import numpy as np

from .base import ErrorMotor, Motor

AUDIO_OUTPUT_SYNCHRONOUS = 2
ESPEAK_RATE, ESPEAK_PITCH = 1, 3
ESPEAK_CHARS_UTF8 = 1
POS_CHARACTER = 1


class MotorEspeakPrueba(Motor):
    nombre = "espeak_prueba"

    def __init__(self, opciones):
        super().__init__(opciones)
        import espeakng_loader
        self._lib = ctypes.cdll.LoadLibrary(espeakng_loader.get_library_path())
        # espeak_Initialize recibe la carpeta que CONTIENE espeak-ng-data. eSpeak NG guarda esa ruta en
        # un búfer de 230 caracteres (N_PATH_HOME): si es más larga, la trunca y cae en la ruta con la
        # que se compiló, que no existe. Con rutas largas se usa un enlace corto temporal.
        datos = os.path.normpath(espeakng_loader.get_data_path())
        padre = os.path.dirname(datos)
        if len(datos) > 200:
            padre = tempfile.mkdtemp(prefix="vzh")
            os.symlink(datos, os.path.join(padre, "espeak-ng-data"))
        self.sr = self._lib.espeak_Initialize(AUDIO_OUTPUT_SYNCHRONOUS, 0, ctypes.c_char_p(padre.encode()), 0)
        if self.sr <= 0:
            raise ErrorMotor("eSpeak NG no se pudo inicializar")
        self._buffer: List[np.ndarray] = []
        TIPO = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.POINTER(ctypes.c_short), ctypes.c_int, ctypes.c_void_p)

        def _recibir(wav, n, _eventos):
            if n > 0:
                self._buffer.append(np.ctypeslib.as_array(wav, shape=(n,)).copy())
            return 0

        self._callback = TIPO(_recibir)  # se guarda para que no lo recoja el recolector
        self._lib.espeak_SetSynthCallback(self._callback)
        self._lib.espeak_Synth.argtypes = [ctypes.c_char_p, ctypes.c_size_t, ctypes.c_uint, ctypes.c_int,
                                           ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]

    def describir(self) -> Dict[str, Any]:
        from importlib.metadata import version
        info = ctypes.c_char_p()
        self._lib.espeak_Info.restype = ctypes.c_char_p
        v = self._lib.espeak_Info(ctypes.byref(info))
        return {"motor": self.nombre, "version": (v or b"?").decode(), "espeakng_loader": version("espeakng-loader"),
                "frecuencia_muestreo": self.sr, "aviso": "motor de prueba de la tubería; no es candidato"}

    def sintetizar(self, texto, voz, idioma, velocidad, nativos):
        if self._lib.espeak_SetVoiceByName(voz.encode()) != 0:
            raise ErrorMotor(f"eSpeak NG no tiene la voz {voz}")
        rate = int(round(175 * float(velocidad or 1.0)))
        pitch = int(nativos.get("pitch", 50))
        self._lib.espeak_SetParameter(ESPEAK_RATE, rate, 0)
        self._lib.espeak_SetParameter(ESPEAK_PITCH, pitch, 0)
        self._buffer = []
        datos = texto.encode("utf-8")
        r = self._lib.espeak_Synth(datos, len(datos) + 1, 0, POS_CHARACTER, 0, ESPEAK_CHARS_UTF8, None, None)
        self._lib.espeak_Synchronize()
        if r != 0 or not self._buffer:
            raise ErrorMotor(f"eSpeak NG no devolvió audio (código {r})")
        audio = np.concatenate(self._buffer).astype(np.float32) / 32768.0
        return audio, int(self.sr), {"rate_ppm": rate, "pitch": pitch, "voz": voz}

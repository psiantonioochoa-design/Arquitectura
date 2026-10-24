"""Posproceso de audio: cambia la señal DESPUÉS de que el motor la genera.

No es un control del motor, y cada muestra lo declara en sus metadatos
(«posproceso»), separado de los «controles_nativos». Métodos, en orden de
preferencia:
  1. ffmpeg con el filtro rubberband (tono con formantes preservados; tempo);
  2. ffmpeg sin rubberband: asetrate + atempo (el tono cambia los formantes);
  3. vocoder de fase en numpy (calidad menor; sin dependencias externas).
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np

from .audio import escribir_wav, leer_wav

_RUBBERBAND = None


def _ffmpeg_tiene_rubberband() -> bool:
    global _RUBBERBAND
    if _RUBBERBAND is None:
        if not shutil.which("ffmpeg"):
            _RUBBERBAND = False
        else:
            r = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True)
            _RUBBERBAND = " rubberband " in r.stdout
    return _RUBBERBAND


def _por_ffmpeg(x, sr: int, filtro: str):
    with tempfile.TemporaryDirectory() as d:
        ent, sal = Path(d) / "e.wav", Path(d) / "s.wav"
        escribir_wav(ent, x, sr)
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(ent), "-af", filtro,
                        "-ar", str(sr), "-ac", "1", "-c:a", "pcm_s16le", str(sal)], check=True)
        y, _ = leer_wav(sal)
    return y


def _estirar(x, factor: float, n_fft: int = 2048, salto: int = 512):
    """Vocoder de fase: factor > 1 alarga (más lento) sin cambiar el tono."""
    ventana = np.hanning(n_fft)
    marcos = [np.fft.rfft(ventana * x[i:i + n_fft]) for i in range(0, len(x) - n_fft, salto)]
    if len(marcos) < 2:
        return x.copy()
    S = np.array(marcos)
    pasos = np.arange(0, len(S) - 1, 1.0 / factor)
    avance = 2 * np.pi * salto * np.arange(S.shape[1]) / n_fft
    fase = np.angle(S[0])
    salida = np.zeros(int(len(pasos) * salto + n_fft))
    for k, p in enumerate(pasos):
        i = int(p)
        a, b = S[i], S[i + 1]
        mag = (1 - (p - i)) * np.abs(a) + (p - i) * np.abs(b)
        trozo = np.fft.irfft(mag * np.exp(1j * fase), n_fft) * ventana
        salida[k * salto:k * salto + n_fft] += trozo
        dfase = np.angle(b) - np.angle(a) - avance
        fase += avance + (dfase - 2 * np.pi * np.round(dfase / (2 * np.pi)))
    salida /= (np.sum(ventana ** 2) / salto)
    return salida.astype(np.float32)


def _remuestrear(x, n: int):
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def aplicar(x, sr: int, tono_semitonos: float = 0.0, tempo: float = 1.0) -> Tuple[Any, Dict[str, Any]]:
    """Devuelve (audio, descripción). tempo > 1 acelera. Si no hay nada que hacer, no toca la señal."""
    if abs(tono_semitonos) < 1e-6 and abs(tempo - 1.0) < 1e-6:
        return x, {}
    tempo = float(min(max(tempo, 0.5), 2.0))
    tono_semitonos = float(min(max(tono_semitonos, -6.0), 6.0))
    factor = 2 ** (tono_semitonos / 12.0)
    desc = {"tono_semitonos": tono_semitonos, "tempo": tempo}
    if shutil.which("ffmpeg") and _ffmpeg_tiene_rubberband():
        y = _por_ffmpeg(x, sr, f"rubberband=pitch={factor:.6f}:tempo={tempo:.6f}:formant=preserved")
        desc["metodo"] = "ffmpeg rubberband (formantes preservados)"
    elif shutil.which("ffmpeg"):
        y = _por_ffmpeg(x, sr, f"asetrate={sr * factor:.3f},aresample={sr},atempo={tempo / factor:.6f}")
        desc["metodo"] = "ffmpeg asetrate+atempo (el cambio de tono desplaza los formantes)"
    else:
        y = _estirar(np.asarray(x, dtype=np.float32), factor / tempo)
        y = _remuestrear(y, int(len(y) / factor))
        desc["metodo"] = "vocoder de fase en numpy (calidad menor)"
    return np.clip(y, -1.0, 1.0), desc

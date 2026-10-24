"""WAV y medidas acústicas objetivas. Se usa dentro de los entornos de los motores (necesita numpy).

Las medidas describen la señal; no dicen si una voz es natural, cálida o
adecuada para Harry. Eso es valoración auditiva del custodio.

  duracion_s, voz_s           duración total y sin silencios al principio y al final
  rms_dbfs, pico_dbfs         nivel medio y de pico; recortes = muestras en ±1.0
  silencio_pct                porcentaje de tramos de 20 ms por debajo de −45 dBFS
  f0_mediana_hz, f0_p10/p90   frecuencia fundamental (YIN) en tramos con voz: es el tono
                              de la voz, no su timbre. Como referencia, en hombres adultos
                              suele andar entre 85 y 155 Hz
  palabras_por_minuto         palabras del texto ÷ voz_s
"""

from __future__ import annotations

import re
import wave
from typing import Any, Dict, Optional

import numpy as np


def escribir_wav(ruta, audio, sr: int) -> None:
    x = np.clip(np.asarray(audio, dtype=np.float32).reshape(-1), -1.0, 1.0)
    with wave.open(str(ruta), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(int(sr))
        w.writeframes((x * 32767.0).astype("<i2").tobytes())


def leer_wav(ruta):
    with wave.open(str(ruta), "rb") as w:
        sr, n, canales, ancho = w.getframerate(), w.getnframes(), w.getnchannels(), w.getsampwidth()
        datos = w.readframes(n)
    if ancho != 2:
        raise ValueError(f"Solo WAV de 16 bits ({ancho * 8} bits en {ruta})")
    x = np.frombuffer(datos, dtype="<i2").astype(np.float32) / 32768.0
    if canales > 1:
        x = x.reshape(-1, canales).mean(axis=1)
    return x, sr


def _db(v: float) -> float:
    return round(20 * np.log10(max(v, 1e-9)), 1)


def _remuestrear(x, sr: int, destino: int):
    if sr == destino:
        return x
    n = int(round(len(x) * destino / sr))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x).astype(np.float32)


def f0_yin(x, sr: int, fmin: float = 50.0, fmax: float = 400.0, umbral: float = 0.15):
    """YIN (de Cheveigné y Kawahara, 2002), sin interpolación parabólica. Devuelve F0 por tramo (0 = sin voz)."""
    x = _remuestrear(x, sr, 16000)
    sr = 16000
    marco, salto = int(0.040 * sr), int(0.010 * sr)
    tau_min, tau_max = int(sr / fmax), int(sr / fmin)
    salida = []
    nfft = 1 << int(np.ceil(np.log2(2 * marco + tau_max)))
    for i in range(0, len(x) - marco - tau_max, salto):
        seg = x[i:i + marco + tau_max]
        a = seg[:marco]
        if np.sqrt(np.mean(a ** 2)) < 10 ** (-40 / 20):
            salida.append(0.0)
            continue
        # d(t) = Σa² + Σb[t:t+marco]² − 2·Σ a·b[t:], con la correlación por FFT
        corr = np.fft.irfft(np.fft.rfft(seg, nfft) * np.conj(np.fft.rfft(a, nfft)), nfft)[:tau_max + 1]
        acum = np.concatenate(([0.0], np.cumsum(seg.astype(np.float64) ** 2)))
        energia_t = acum[np.arange(tau_max + 1) + marco] - acum[np.arange(tau_max + 1)]
        d = np.maximum(np.sum(a.astype(np.float64) ** 2) + energia_t - 2 * corr, 0.0)
        acumulado = np.cumsum(d[1:])
        cmnd = np.ones_like(d)
        cmnd[1:] = d[1:] * np.arange(1, len(d)) / np.where(acumulado == 0, 1e-12, acumulado)
        candidatos = np.where(cmnd[tau_min:] < umbral)[0]
        if not len(candidatos):
            salida.append(0.0)
            continue
        t = candidatos[0] + tau_min
        while t + 1 < len(cmnd) and cmnd[t + 1] < cmnd[t]:
            t += 1
        salida.append(sr / t)
    return np.array(salida)


def medidas(x, sr: int, texto: Optional[str] = None) -> Dict[str, Any]:
    x = np.asarray(x, dtype=np.float32).reshape(-1)
    duracion = len(x) / sr if sr else 0.0
    tramo = max(1, int(0.020 * sr))
    n = len(x) // tramo
    energia = np.sqrt(np.mean(x[: n * tramo].reshape(n, tramo) ** 2, axis=1)) if n else np.array([0.0])
    activos = np.where(energia > 10 ** (-45 / 20))[0]
    voz_s = ((activos[-1] - activos[0] + 1) * tramo / sr) if len(activos) else 0.0
    f0 = f0_yin(x, sr)
    con_voz = f0[f0 > 0]
    palabras = len(re.findall(r"\w+", texto)) if texto else None
    return {
        "frecuencia_muestreo": int(sr),
        "duracion_s": round(duracion, 3),
        "voz_s": round(voz_s, 3),
        "rms_dbfs": _db(float(np.sqrt(np.mean(x ** 2))) if len(x) else 0.0),
        "pico_dbfs": _db(float(np.max(np.abs(x))) if len(x) else 0.0),
        "recortes": int(np.sum(np.abs(x) >= 0.999)),
        "silencio_pct": round(100.0 * float(np.mean(energia <= 10 ** (-45 / 20))), 1),
        "f0_mediana_hz": round(float(np.median(con_voz)), 1) if len(con_voz) else None,
        "f0_p10_hz": round(float(np.percentile(con_voz, 10)), 1) if len(con_voz) else None,
        "f0_p90_hz": round(float(np.percentile(con_voz, 90)), 1) if len(con_voz) else None,
        "tramos_con_voz_pct": round(100.0 * len(con_voz) / len(f0), 1) if len(f0) else 0.0,
        "palabras_por_minuto": round(palabras / voz_s * 60, 1) if (palabras and voz_s) else None,
        "audio_vacio": bool(not len(activos)),
    }

"""Identifica el equipo real en que se genera cada muestra.

Cada WAV lleva esta etiqueta: una muestra hecha en la nube nunca se presenta
como medición del M4. Solo biblioteca estándar; no cambia nada del sistema.
"""

from __future__ import annotations

import os
import platform
import re
import subprocess
from typing import Any, Dict


def _salida(orden) -> str:
    try:
        return subprocess.run(orden, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception:
        return ""


def describir() -> Dict[str, Any]:
    sistema = platform.system()
    maquina = platform.machine()
    cpu, ram_gb, gpu = "desconocido", None, "no detectada"
    if sistema == "Darwin":
        cpu = _salida(["sysctl", "-n", "machdep.cpu.brand_string"]) or "desconocido"
        memsize = _salida(["sysctl", "-n", "hw.memsize"])
        ram_gb = round(int(memsize) / 2**30, 1) if memsize.isdigit() else None
        gpu = "GPU integrada de Apple (Metal); su uso depende del motor" if maquina == "arm64" else "no detectada"
        version = platform.mac_ver()[0]
    else:
        try:
            with open("/proc/cpuinfo", encoding="utf-8") as f:
                m = re.search(r"model name\s*:\s*(.+)", f.read())
                cpu = m.group(1).strip() if m else cpu
            with open("/proc/meminfo", encoding="utf-8") as f:
                m = re.search(r"MemTotal:\s*(\d+)", f.read())
                ram_gb = round(int(m.group(1)) / 2**20, 1) if m else None
        except OSError:
            pass
        if _salida(["nvidia-smi", "-L"]):
            gpu = "NVIDIA: " + _salida(["nvidia-smi", "-L"]).splitlines()[0]
        version = platform.release()
    es_mac_apple = sistema == "Darwin" and maquina == "arm64"
    nube = bool(os.environ.get("CLAUDE_CODE_REMOTE") or os.environ.get("CCR_SESSION")) or (sistema == "Linux" and not es_mac_apple)
    etiqueta = (f"mac-{maquina}" if sistema == "Darwin" else f"{'nube' if nube else 'equipo'}-{sistema.lower()}-{maquina}")
    return {
        "etiqueta": etiqueta,
        "sistema": f"{sistema} {version}",
        "arquitectura": maquina,
        "cpu": cpu,
        "nucleos": os.cpu_count(),
        "ram_gb": ram_gb,
        "gpu": gpu,
        "es_equipo_de_destino": False,  # solo el custodio lo confirma, en su Mac
        "aviso": ("Medido en la nube: NO es una medición de la MacBook Air M4." if etiqueta.startswith("nube")
                  else "Equipo local; confirma que es el de destino antes de usar estas cifras como del M4."),
    }

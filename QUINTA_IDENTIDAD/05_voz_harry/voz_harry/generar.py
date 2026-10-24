"""Genera las muestras de comparación y su índice.

Cada muestra: muestras/<equipo>/<motor>/<motor>__<voz>__<idioma>__<prueba>.wav y un
.json al lado con parámetros, tiempos, memoria, medidas y equipo. El índice
muestras/<equipo>/indice.csv resume todas las de ese equipo.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import catalogo, equipo, rutas
from .cliente import ClienteMotor, ErrorCliente

COLUMNAS = ["equipo", "motor", "voz", "idioma", "prueba", "archivo", "duracion_s", "sintesis_s", "factor_tiempo_real",
            "incluye_carga_de_voz", "carga_motor_s", "rss_max_proceso_mb", "f0_mediana_hz", "f0_p10_hz", "f0_p90_hz",
            "palabras_por_minuto", "rms_dbfs", "pico_dbfs", "recortes", "posproceso", "controles_nativos",
            "experimental", "prueba_de_tuberia", "sin_conexion_hf"]


def carpeta_equipo() -> Path:
    return rutas.muestras() / equipo.describir()["etiqueta"]


def fila(meta: Dict[str, Any], voz: Dict[str, Any]) -> Dict[str, Any]:
    m, t = meta["medidas"], meta["tiempos"]
    return {
        "equipo": meta["equipo"]["etiqueta"], "motor": meta["motor"], "voz": catalogo.clave_voz(voz),
        "idioma": meta["idioma"], "prueba": meta["contexto"].get("prueba", ""), "archivo": meta["archivo"],
        "duracion_s": m["duracion_s"], "sintesis_s": t["sintesis_s"], "factor_tiempo_real": t["factor_tiempo_real"],
        "incluye_carga_de_voz": t["incluye_carga_de_voz"], "carga_motor_s": t["carga_motor_s"],
        "rss_max_proceso_mb": meta["memoria"]["rss_max_proceso_mb"],
        "f0_mediana_hz": m["f0_mediana_hz"], "f0_p10_hz": m["f0_p10_hz"], "f0_p90_hz": m["f0_p90_hz"],
        "palabras_por_minuto": m["palabras_por_minuto"], "rms_dbfs": m["rms_dbfs"], "pico_dbfs": m["pico_dbfs"],
        "recortes": m["recortes"], "posproceso": json.dumps(meta["posproceso"], ensure_ascii=False),
        "controles_nativos": json.dumps(meta["controles_nativos"], ensure_ascii=False),
        "experimental": bool(voz.get("experimental")), "prueba_de_tuberia": bool(voz.get("prueba_de_tuberia")),
        "sin_conexion_hf": meta["sin_conexion_hf"],
    }


def reescribir_indice(base: Path) -> Path:
    """Reconstruye indice.csv desde los .json de la carpeta (las muestras de la interfaz no entran)."""
    voces = {(v["motor"], v["id"], v.get("variante")): v for v in catalogo.cargar()["voces"]}
    filas = []
    for j in sorted(base.glob("*/*.json")):
        meta = json.loads(j.read_text(encoding="utf-8"))
        if meta.get("formato") != "voz_harry/muestra 1" or not meta["contexto"].get("prueba"):
            continue
        v = voces.get((meta["motor"], meta["voz"], meta["contexto"].get("variante"))) or {"id": meta["voz"]}
        filas.append(fila(meta, v))
    destino = base / "indice.csv"
    with open(destino, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS)
        w.writeheader()
        w.writerows(filas)
    return destino


def generar(motor: str, opciones: Optional[Dict[str, Any]] = None, ids_voces: Optional[List[str]] = None,
            ids_textos: Optional[List[str]] = None, velocidad: float = 1.0, incluir_experimentales: bool = True,
            avance=print) -> List[Dict[str, Any]]:
    voces = [v for v in catalogo.voces(motor, incluir_experimentales, incluir_pruebas=True)
             if not ids_voces or v["id"] in ids_voces or catalogo.clave_voz(v) in ids_voces]
    if not voces:
        raise ErrorCliente(f"No hay voces de {motor} con ese filtro")
    base = carpeta_equipo()
    hechas = []
    with ClienteMotor(motor, opciones) as c:
        for v, t in catalogo.combinaciones(voces, ids_textos):
            destino = base / motor / catalogo.nombre_muestra(motor, v, t["idioma"], t["id"])
            nativos = {"lang_code": v["lang_code"]} if v.get("lang_code") else {}
            try:
                meta = c.sintetizar(texto=t["texto"], voz=v["id"], idioma=t["idioma"], velocidad=velocidad,
                                    nativos=nativos, salida_wav=str(destino),
                                    contexto={"prueba": t["id"], "nombre_prueba": t["nombre"], "variante": v.get("variante"),
                                              "experimental": bool(v.get("experimental"))})
            except ErrorCliente as e:
                avance(f"  ERROR {motor} {catalogo.clave_voz(v)} {t['id']}: {e}")
                continue
            hechas.append(meta)
            avance(f"  {destino.relative_to(rutas.raiz())} · {meta['medidas']['duracion_s']} s de audio en "
                   f"{meta['tiempos']['sintesis_s']} s · F0 {meta['medidas']['f0_mediana_hz']} Hz")
    reescribir_indice(base)
    return hechas


def comprobar_muestra(meta: Dict[str, Any]) -> List[str]:
    """Comprobaciones objetivas mínimas de que una muestra es audio real y usable."""
    m, problemas = meta["medidas"], []
    if m["audio_vacio"]:
        problemas.append("el audio está vacío o es silencio")
    if m["duracion_s"] < 0.5:
        problemas.append(f"duración sospechosa: {m['duracion_s']} s")
    if m["recortes"] > 0.001 * m["duracion_s"] * m["frecuencia_muestreo"]:
        problemas.append(f"{m['recortes']} muestras recortadas")
    if m["tramos_con_voz_pct"] < 10:  # YIN (umbral 0.15) es estricto: la mediana de F0 es estable, la fracción no
        problemas.append(f"poca voz detectada ({m['tramos_con_voz_pct']} % de tramos)")
    if m["palabras_por_minuto"] and not 60 <= m["palabras_por_minuto"] <= 260:
        problemas.append(f"ritmo fuera de rango: {m['palabras_por_minuto']} palabras por minuto")
    return problemas

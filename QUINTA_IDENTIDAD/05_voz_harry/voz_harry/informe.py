"""Informe de comparación: medidas objetivas por equipo y, aparte, la valoración auditiva del custodio.

Nunca mezcla las dos cosas: las medidas salen de los .json de las muestras y la
valoración solo de evaluacion/valoraciones.csv, que llena el custodio desde la
interfaz. Si no hay valoraciones, lo dice.
"""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, List

from . import rutas


def _muestras(etiqueta: str) -> List[Dict[str, Any]]:
    salida = []
    for j in sorted((rutas.muestras() / etiqueta).glob("*/*.json")):
        meta = json.loads(j.read_text(encoding="utf-8"))
        if meta.get("formato") == "voz_harry/muestra 1" and (meta.get("contexto") or {}).get("prueba"):
            meta["_ruta"] = j.with_suffix(".wav").relative_to(rutas.muestras()).as_posix()
            salida.append(meta)
    return salida


def _valoraciones() -> List[Dict[str, str]]:
    archivo = rutas.evaluacion() / "valoraciones.csv"
    if not archivo.exists():
        return []
    with open(archivo, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def escribir(etiqueta: str) -> Path:
    muestras = _muestras(etiqueta)
    if not muestras:
        raise ValueError(f"No hay muestras de prueba en muestras/{etiqueta}/")
    eq = muestras[0]["equipo"]
    L = [f"# Comparación de voces · equipo `{etiqueta}`", "",
         f"Generado: {datetime.now().isoformat(timespec='seconds')}. Equipo: {eq['sistema']}, {eq['cpu']}, "
         f"{eq['ram_gb']} GB, GPU: {eq['gpu']}.", "", f"> {eq['aviso']}", "",
         "## 1. Mediciones objetivas", "",
         "Tiempos de síntesis medidos de pared en el trabajador. La primera muestra de cada voz incluye cargarla. "
         "La memoria es el pico del proceso del motor desde que arrancó: incluye el modelo. F0 es el tono "
         "fundamental (YIN) en tramos con voz; describe la altura de la voz, no su timbre ni su calidez.", "",
         "| Motor | Voz | Idioma | Prueba | Audio (s) | Síntesis (s) | Factor t. real | Memoria pico (MB) | F0 mediana (Hz) | F0 p10–p90 | Palabras/min | Posproceso |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for m in sorted(muestras, key=lambda m: (m["motor"], m["voz"], m["idioma"], m["contexto"]["prueba"])):
        me, t = m["medidas"], m["tiempos"]
        marca = " (experimental)" if m["contexto"].get("experimental") else ""
        L.append(f"| {m['motor']} | {m['voz']}{marca} | {m['idioma']} | {m['contexto']['prueba']} | {me['duracion_s']} | "
                 f"{t['sintesis_s']}{' *' if t['incluye_carga_de_voz'] else ''} | {t['factor_tiempo_real']} | "
                 f"{m['memoria']['rss_max_proceso_mb']} | {me['f0_mediana_hz']} | {me['f0_p10_hz']}–{me['f0_p90_hz']} | "
                 f"{me['palabras_por_minuto']} | {'no' if m['posproceso'] == 'ninguno' else 'sí'} |")
    L += ["", "\\* incluye la carga de la voz o del modelo en esa primera síntesis.", "",
          "### Resumen por voz", "",
          "| Motor | Voz | Muestras | Factor t. real (mediana, sin primeras) | Memoria pico máx. (MB) | F0 mediana ES (Hz) | F0 mediana EN (Hz) |",
          "|---|---|---|---|---|---|---|"]
    grupos = defaultdict(list)
    for m in muestras:
        grupos[(m["motor"], m["voz"])].append(m)
    for (motor, voz), ms in sorted(grupos.items()):
        rtf = [m["tiempos"]["factor_tiempo_real"] for m in ms if not m["tiempos"]["incluye_carga_de_voz"] and m["tiempos"]["factor_tiempo_real"]]
        f0 = {i: [m["medidas"]["f0_mediana_hz"] for m in ms if m["idioma"] == i and m["medidas"]["f0_mediana_hz"]] for i in ("es", "en")}
        L.append(f"| {motor} | {voz} | {len(ms)} | {round(median(rtf), 3) if rtf else '—'} | "
                 f"{max(m['memoria']['rss_max_proceso_mb'] for m in ms)} | {round(median(f0['es']), 1) if f0['es'] else '—'} | "
                 f"{round(median(f0['en']), 1) if f0['en'] else '—'} |")
    L += ["", "Una F0 parecida en español y en inglés para la misma voz es solo un indicio de consistencia; el timbre se juzga escuchando.", "",
          "## 2. Valoración auditiva del custodio", ""]
    rutas_eq = {m["_ruta"] for m in muestras}
    vals = [v for v in _valoraciones() if v.get("muestra") in rutas_eq]
    if not vals:
        L += ["**Todavía no hay valoraciones de estas muestras.** Ninguna afirmación sobre naturalidad, calidez, edad aparente, "
              "acento o expresividad se puede hacer sin escuchar. Valóralas en la interfaz (`python3 voz.py interfaz`), "
              "de preferencia con la escucha a ciegas.", ""]
    else:
        por = defaultdict(list)
        for v in vals:
            m = next(x for x in muestras if x["_ruta"] == v["muestra"])
            por[(m["motor"], m["voz"])].append(v)
        L += ["| Motor | Voz | Valoraciones | Naturalidad | Inteligibilidad | Calidez | Expresividad | Edad aparente (más citada) | Timbre (más citado) | Solemne/teatral |",
              "|---|---|---|---|---|---|---|---|---|---|"]
        for (motor, voz), vs in sorted(por.items()):
            def prom(c):
                xs = [_num(v.get(c)) for v in vs if _num(v.get(c)) is not None]
                return round(mean(xs), 1) if xs else "—"

            def moda(c):
                xs = [v.get(c) for v in vs if v.get(c)]
                return max(set(xs), key=xs.count) if xs else "—"
            L.append(f"| {motor} | {voz} | {len(vs)} | {prom('naturalidad_1_5')} | {prom('inteligibilidad_1_5')} | {prom('calidez_1_5')} | "
                     f"{prom('expresividad_1_5')} | {moda('edad_aparente')} | {moda('timbre')} | {moda('solemne_o_teatral')} |")
        L.append("")
    destino = rutas.evaluacion() / f"comparacion_{etiqueta}.md"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text("\n".join(L) + "\n", encoding="utf-8")
    return destino

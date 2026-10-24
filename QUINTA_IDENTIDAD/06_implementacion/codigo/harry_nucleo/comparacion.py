"""Comparación preliminar entre corridas exploratorias (por ejemplo, dos modelos).

Produce, en una carpeta nueva:
  comparacion.md          medidas técnicas por modelo y respuestas LITERALES por caso
  comparacion_ciega.csv   las mismas respuestas evaluadas, con etiquetas A/B al azar,
                          para calificar sin saber de qué modelo vienen (§4.5 del
                          conjunto de pruebas)
  clave_ciega.json        qué modelo es A y cuál B en cada fila (no abrir antes de calificar)

No califica ni declara conformidad. Solo usa respuestas completas del intento que
terminó cada unidad; las incompletas se cuentan, nunca se presentan como completas.
"""

from __future__ import annotations

import csv
import random
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, List

from .prefiltro import prefiltrar
from .util import ahora_iso, escribir_json, leer_json, leer_jsonl

AVISO = ("COMPARACIÓN PRELIMINAR de corridas exploratorias. No es una evaluación de conformidad ni una "
         "calificación: describe lo que respondieron los modelos y deja el juicio a quien califica.")


def _validas(carpeta: Path):
    validos = {}
    unidades = [u for u in leer_jsonl(carpeta / "unidades.jsonl") if "unidad" in u]
    for u in unidades:
        if u.get("estado") == "completa":
            validos[u["unidad"]] = u["intento"]
    resp = [r for r in leer_jsonl(carpeta / "respuestas.jsonl") if "unidad" in r]
    return unidades, resp, validos


def medidas(carpeta: Path) -> Dict[str, Any]:
    man = leer_json(carpeta / "manifiesto.json")
    unidades, resp, validos = _validas(carpeta)
    ultimos = {}
    for u in unidades:
        ultimos[u["unidad"]] = u
    estados = Counter(ultimos.get(u, {}).get("estado", "sin correr") for u in man["unidades_planeadas"])
    completas = [r for r in resp if r.get("estado") == "completa"]
    met = [r.get("metricas") or {} for r in completas]
    pre = prefiltrar(carpeta)
    terminaciones = Counter(((r.get("metricas") or {}).get("done_reason") or r.get("nota") or "—") for r in resp)
    def serie(clave):
        return [m[clave] for m in met if m.get(clave) is not None]
    dur = [r["duracion_s"] for r in completas]
    pt = [r["primer_token_s"] for r in completas if r.get("primer_token_s") is not None]
    return {
        "corrida": man["corrida"], "modelo": man["plataforma"]["adaptador"].get("modelo"),
        "tipo": man.get("tipo"), "estado": man.get("estado"),
        "opciones": man["plataforma"]["adaptador"].get("opciones"),
        "think": man["plataforma"]["adaptador"].get("think"),
        "version_ollama": next((s.get("adaptador", {}).get("version_ollama") for s in man.get("sesiones", [])
                                if s.get("adaptador", {}).get("version_ollama")), None),
        "digest_modelo": next((s.get("adaptador", {}).get("digest_modelo") for s in man.get("sesiones", [])
                               if s.get("adaptador", {}).get("digest_modelo")), None),
        "instrucciones": f"{man['nucleo'].get('version_instrucciones')} ({man['nucleo']['hash_instrucciones'][:12]})",
        "unidades": dict(estados), "respuestas": len(resp), "completas": len(completas),
        "terminaciones": dict(terminaciones),
        "duracion_s": {"media": round(mean(dur), 2) if dur else None, "mediana": round(median(dur), 2) if dur else None,
                       "max": round(max(dur), 2) if dur else None},
        "primer_token_s_mediana": round(median(pt), 2) if pt else None,
        "prompt_eval_count": {"media": round(mean(serie("prompt_eval_count"))) if serie("prompt_eval_count") else None,
                              "max": max(serie("prompt_eval_count"), default=None)},
        "eval_count": {"media": round(mean(serie("eval_count"))) if serie("eval_count") else None,
                       "max": max(serie("eval_count"), default=None)},
        "tokens_por_segundo_media": round(mean(serie("tokens_por_segundo")), 1) if serie("tokens_por_segundo") else None,
        "errores": dict(Counter(e["tipo"] for e in leer_jsonl(carpeta / "errores.jsonl") if "tipo" in e)),
        "prefiltro": {"revisadas": pre["revisadas"], "con_cierre_m4": pre["con_cierre_m4"],
                      "senales": dict(Counter(a["regla"] for a in pre["alertas"] if a["regla"] != "M4-cierre"))},
        "_respuestas": resp, "_validos": validos, "_alertas": pre["alertas"],
    }


def comparar(carpetas: List[Path], destino: Path, semilla: int = 20261024) -> Path:
    destino.mkdir(parents=True, exist_ok=False)
    datos = [medidas(c) for c in carpetas]
    casos = {c["id"]: c for c in leer_json(carpetas[0] / "entradas" / "casos_ejecutables.json")["casos"]}
    # respuestas evaluadas y válidas: (caso, variante, repetición, turno) -> {modelo: respuesta}
    tabla: Dict[tuple, Dict[str, Dict[str, Any]]] = defaultdict(dict)
    for d in datos:
        for r in d["_respuestas"]:
            if r.get("evaluado") and r.get("estado") == "completa" and d["_validos"].get(r["unidad"]) == r["intento"]:
                tabla[(r["caso"], r["variante"], r["repeticion"], r["turno"])][d["modelo"]] = r
    modelos = [d["modelo"] for d in datos]

    L = ["# Comparación preliminar entre modelos", "", f"> {AVISO}", "",
         f"Generada: {ahora_iso()}. Corridas: {', '.join('`' + d['corrida'] + '`' for d in datos)}.", "",
         "**Si vas a calificar a ciegas, hazlo primero con `comparacion_ciega.csv` y lee este documento después:** "
         "aquí cada respuesta lleva el nombre de su modelo.", "",
         "## Condiciones", "", "| | " + " | ".join(modelos) + " |", "|---|" + "---|" * len(modelos)]
    for clave, titulo in (("version_ollama", "Ollama"), ("digest_modelo", "Digest del modelo"), ("instrucciones", "Instrucciones"),
                          ("think", "think"), ("opciones", "Opciones")):
        L.append(f"| {titulo} | " + " | ".join(str(d.get(clave)) for d in datos) + " |")
    L += ["", "## Medidas técnicas (objetivas)", "", "| Medida | " + " | ".join(modelos) + " |", "|---|" + "---|" * len(modelos)]
    filas = [
        ("Unidades por estado", lambda d: ", ".join(f"{k}: {v}" for k, v in sorted(d["unidades"].items()))),
        ("Respuestas registradas / completas", lambda d: f"{d['respuestas']} / {d['completas']}"),
        ("Terminaciones (done_reason o nota)", lambda d: ", ".join(f"{k}: {v}" for k, v in sorted(d["terminaciones"].items()))),
        ("Duración por respuesta, s (media · mediana · máx.)", lambda d: f"{d['duracion_s']['media']} · {d['duracion_s']['mediana']} · {d['duracion_s']['max']}"),
        ("Primer token, s (mediana)", lambda d: str(d["primer_token_s_mediana"])),
        ("prompt_eval_count (media · máx.)", lambda d: f"{d['prompt_eval_count']['media']} · {d['prompt_eval_count']['max']}"),
        ("eval_count (media · máx.)", lambda d: f"{d['eval_count']['media']} · {d['eval_count']['max']}"),
        ("Tokens por segundo (media)", lambda d: str(d["tokens_por_segundo_media"])),
        ("Errores", lambda d: ", ".join(f"{k}: {v}" for k, v in d["errores"].items()) or "ninguno"),
        ("Prefiltro: cierre con pregunta u oferta (M-4)", lambda d: f"{d['prefiltro']['con_cierre_m4']} de {d['prefiltro']['revisadas']}"),
        ("Prefiltro: otras señales", lambda d: ", ".join(f"{k}: {v}" for k, v in sorted(d["prefiltro"]["senales"].items())) or "ninguna"),
    ]
    for titulo, f in filas:
        L.append(f"| {titulo} | " + " | ".join(f(d) for d in datos) + " |")
    L += ["", "Las señales del prefiltro son preguntas para quien califica, no fallas. Las respuestas incompletas "
          "(por ejemplo `done_reason=length`) no se cuentan como completas ni aparecen abajo.", "",
          "## Respuestas literales (turnos evaluados)", ""]
    alertas = defaultdict(list)
    for d in datos:
        for a in d["_alertas"]:
            alertas[(d["modelo"], a["unidad"], a["turno"])].append(a["regla"])
    for (cid, var, rep, turno) in sorted(tabla, key=lambda k: (list(casos).index(k[0]) if k[0] in casos else 999, k[1], k[2], k[3])):
        c = casos.get(cid, {})
        por_modelo = tabla[(cid, var, rep, turno)]
        cualquiera = next(iter(por_modelo.values()))
        L += [f"### {cid} · variante {var} · repetición {rep} · turno {turno}", "",
              f"Bloque {c.get('bloque')} · criticidad {c.get('criticidad')} · forma {c.get('forma')}", "",
              "**Persona:** " + cualquiera["mensaje_usuario"].replace("\n", " "), ""]
        for m in modelos:
            r = por_modelo.get(m)
            if r is None:
                L += [f"**{m}:** _sin respuesta completa válida para esta unidad_", ""]
                continue
            met = r.get("metricas") or {}
            senales = alertas.get((m, r["unidad"], r["turno"])) or []
            L += [f"**{m}** · {r['duracion_s']} s · {met.get('eval_count')} tokens · done_reason={met.get('done_reason')}"
                  + (f" · prefiltro: {', '.join(senales)}" if senales else ""), ""]
            L += ["> " + linea if linea.strip() else ">" for linea in r["respuesta"].splitlines()] + [""]
    (destino / "comparacion.md").write_text("\n".join(L) + "\n", encoding="utf-8")

    azar = random.Random(semilla)
    clave = []
    with open(destino / "comparacion_ciega.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["fila", "caso", "variante", "repeticion", "turno", "situacion", "mensaje_usuario",
                    "respuesta_A", "respuesta_B", "conducta_que_cumple", "fallas_que_lo_delatan",
                    "calificacion_A_0_1_2", "calificacion_B_0_1_2", "notas"])
        fila = 0
        for k in sorted(tabla):
            por_modelo = tabla[k]
            if len(por_modelo) < 2:
                continue
            orden = list(por_modelo)[:2]
            azar.shuffle(orden)
            fila += 1
            c = casos[k[0]]
            w.writerow([fila, k[0], k[1], k[2], k[3], c["evaluacion"]["situacion"], por_modelo[orden[0]]["mensaje_usuario"],
                        por_modelo[orden[0]]["respuesta"], por_modelo[orden[1]]["respuesta"],
                        c["evaluacion"]["cumple"], c["evaluacion"]["fallas"], "", "", ""])
            clave.append({"fila": fila, "A": orden[0], "B": orden[1]})
    escribir_json(destino / "clave_ciega.json", {"semilla": semilla, "aviso": "No abrir antes de calificar.", "filas": clave})
    return destino

"""Resumen técnico de una corrida y hoja de calificación humana.

Nada aquí califica a Harry. El resumen cuenta unidades, tiempos y errores.
La hoja prepara la calificación humana con los estados del plan:
pendiente, cumple, parcial, falla, no evaluable.
"""

from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from statistics import mean, median
from typing import Any, Dict, List

from .util import leer_json, leer_jsonl

ESTADOS_HOJA = ("pendiente", "cumple", "parcial", "falla", "no evaluable")


def tipo_de(man: Dict[str, Any]) -> str:
    """Las corridas de la etapa 1 no tenían 'tipo'; todas eran simulaciones técnicas."""
    return man.get("tipo") or ("simulacion_tecnica" if man.get("modo") == "simulacion_tecnica" else "exploratoria")


BANDERAS = {
    "simulacion_tecnica": "# ⚠️ SIMULACIÓN TÉCNICA — NO ES UNA EVALUACIÓN DE HARRY",
    "exploratoria": "# CORRIDA EXPLORATORIA — DIAGNÓSTICO PRELIMINAR, NO ES CONFORMIDAD",
    "conformidad": "# EVALUACIÓN DE CONFORMIDAD",
}


def _datos(carpeta: Path):
    man = leer_json(carpeta / "manifiesto.json")
    casos = {c["id"]: c for c in leer_json(carpeta / "entradas" / "casos_ejecutables.json")["casos"]}
    unidades = [r for r in leer_jsonl(carpeta / "unidades.jsonl") if "unidad" in r]
    respuestas = [r for r in leer_jsonl(carpeta / "respuestas.jsonl") if "unidad" in r]
    errores = [r for r in leer_jsonl(carpeta / "errores.jsonl") if "unidad" in r]
    return man, casos, unidades, respuestas, errores


def _ultimo_intento_completo(unidades: List[Dict[str, Any]]) -> Dict[str, int]:
    """unidad -> número del intento que terminó completo (el último, si hubo varios)."""
    salida: Dict[str, int] = {}
    for r in unidades:
        if r.get("estado") == "completa":
            salida[r["unidad"]] = r["intento"]
    return salida


def resumen_texto(carpeta: Path) -> str:
    man, casos, unidades, respuestas, errores = _datos(carpeta)
    plan = man["unidades_planeadas"]
    ultimos: Dict[str, Dict[str, Any]] = {}
    for r in unidades:
        ultimos[r["unidad"]] = r
    estados = Counter(ultimos.get(u, {}).get("estado", "sin correr") for u in plan)
    simulada = man["modo"] == "simulacion_tecnica"
    tipo = tipo_de(man)
    L: List[str] = [BANDERAS[tipo], ""]
    L += [f"# Resumen técnico de la corrida `{man['corrida']}`", ""]
    L += [f"> {man['aviso']}", ""]
    L += [
        f"- **Tipo:** {tipo} · **Estado:** {man['estado']}",
        f"- **Plataforma:** {man['plataforma']['id']} ({man['plataforma']['adaptador'].get('tipo')})",
        f"- **Modelo:** {man['plataforma']['adaptador'].get('modelo', 'ninguno')}",
        f"- **Instrucciones:** estado «{man['nucleo']['estado_instrucciones']}», versión {man['nucleo'].get('version_instrucciones', '—')}, huella {man['nucleo']['hash_instrucciones'][:12]}",
        f"- **Casos:** {len(man['seleccion']['casos'])} · **repeticiones:** {man['repeticiones']} · **unidades planeadas:** {len(plan)}",
        f"- **Sesiones de ejecución:** {len(man.get('sesiones', []))}",
        "",
        "## Unidades",
        "",
        "| Estado | Unidades |",
        "|---|---|",
    ]
    for est in ("completa", "incompleta", "error", "interrumpida", "sin correr"):
        if estados.get(est):
            L.append(f"| {est} | {estados[est]} |")
    L.append("")
    montajes = [r["montaje"] for r in respuestas if r.get("montaje")]
    if montajes:
        tot = [m["total_estimado"] for m in montajes]
        omit = sum(1 for m in montajes if m["intercambios_omitidos"])
        sinref = sum(1 for m in montajes if m["referencias_quitadas_por_espacio"])
        L += [
            "## Contexto enviado (estimación)",
            "",
            f"Tokens estimados por llamada: media {mean(tot):.0f} · máximo {max(tot)} · ventana {man['nucleo'].get('ventana_tokens', '—')} "
            f"· reserva para la respuesta {man['nucleo'].get('reserva_respuesta_tokens', '—')}. "
            f"Llamadas con intercambios omitidos por espacio: {omit}. Llamadas sin referencias por espacio: {sinref}.",
            "",
        ]
    tiempos = [r["duracion_s"] for r in respuestas if r.get("estado") == "completa"]
    if tiempos:
        L += [
            "## Tiempos por respuesta",
            "",
            f"Respuestas registradas: {len(respuestas)} · completas: {len(tiempos)} · "
            f"media {mean(tiempos):.3f} s · mediana {median(tiempos):.3f} s · máximo {max(tiempos):.3f} s",
            "",
        ]
        tps = [r["metricas"].get("tokens_por_segundo") for r in respuestas if r.get("metricas", {}).get("tokens_por_segundo")]
        if tps:
            L += [f"Tokens por segundo: media {mean(tps):.1f}", ""]
    if respuestas and not simulada:
        term = Counter(((r.get("metricas") or {}).get("done_reason") or r.get("nota") or "sin dato") for r in respuestas)
        incompletas = [r for r in respuestas if r.get("estado") != "completa"]
        L += ["## Terminaciones", "",
              "| Terminación (done_reason o nota) | Respuestas |", "|---|---|"]
        L += [f"| {k} | {v} |" for k, v in term.most_common()]
        L += ["", f"Respuestas incompletas (cortadas, por tiempo o por `num_predict`): {len(incompletas)}. "
              "**No se cuentan como completas** ni entran en la hoja de calificación.", ""]
        reales = [(r["montaje"]["total_estimado"], r["metricas"]["prompt_eval_count"]) for r in respuestas
                  if (r.get("metricas") or {}).get("prompt_eval_count") and r.get("montaje")]
        salida = [r["metricas"]["eval_count"] for r in respuestas if (r.get("metricas") or {}).get("eval_count")]
        if reales:
            L += ["## Tokens reales", "",
                  f"prompt_eval_count: media {mean(t for _, t in reales):.0f} · máximo {max(t for _, t in reales)}. "
                  f"Estimado ÷ real: mínimo {min(e / t for e, t in reales):.2f} · mediana {median(e / t for e, t in reales):.2f}. "
                  + (f"eval_count: media {mean(salida):.0f} · máximo {max(salida)}. " if salida else "")
                  + "El detalle está en `harry calibrar`.", ""]
    if errores:
        L += ["## Errores", "", "| Tipo | Veces |", "|---|---|"]
        for tipo, n in Counter(e["tipo"] for e in errores).most_common():
            L.append(f"| {tipo} | {n} |")
        L.append("")
    excl = man["seleccion"].get("excluidos_por_anexo_A") or []
    incl_pend = [c for c in man["seleccion"]["casos"] if casos[c]["pendiente_anexo_A"]]
    L += ["## Anexo A", ""]
    if excl:
        L.append(f"Excluidos de esta corrida por depender del Anexo A no aprobado ({len(excl)}): {', '.join(excl)}.")
    if incl_pend:
        L.append(
            f"Incluidos solo para registrar respuestas ({len(incl_pend)}): {', '.join(incl_pend)}. "
            "**Quedan pendientes: no se califican ni cuentan como aprobados hasta aprobar el Anexo A.**"
        )
    if not excl and not incl_pend:
        L.append("La selección no tocaba casos del Anexo A.")
    L += [
        "",
        "## Lo que este resumen no dice",
        "",
        "No califica respuestas ni declara conformidad. La calificación es humana (hoja `calificacion.csv`) "
        "y los umbrales del conjunto de pruebas siguen en propuesta.",
    ]
    if simulada:
        L += ["", "**Todas las respuestas de esta corrida son simuladas. No contienen ninguna conducta de Harry.**"]
    return "\n".join(L) + "\n"


def escribir_resumen(carpeta: Path) -> Path:
    destino = carpeta / "resumen.md"
    destino.write_text(resumen_texto(carpeta), encoding="utf-8")
    return destino


def escribir_hoja(carpeta: Path) -> Path:
    man, casos, unidades, respuestas, _ = _datos(carpeta)
    simulada = man["modo"] == "simulacion_tecnica"
    tipo = tipo_de(man)
    validos = _ultimo_intento_completo(unidades)
    destino = carpeta / "calificacion.csv"
    columnas = [
        "corrida", "unidad", "caso", "variante", "repeticion", "turno", "criticidad", "bloque",
        "depende_de", "situacion", "mensaje_usuario", "respuesta", "conducta_que_cumple",
        "fallas_que_lo_delatan", "comparar_con_otra_variante", "estado", "motivo_estado",
        "calificacion_0_1_2", "consistencia_par_si_no", "notas",
    ]
    filas = 0
    with open(destino, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(columnas)
        for r in respuestas:
            if not r.get("evaluado"):
                continue
            if validos.get(r["unidad"]) != r["intento"]:
                continue  # solo el intento que terminó completo
            c = casos[r["caso"]]
            if simulada:
                estado, motivo = "no evaluable", "simulación técnica: la respuesta no viene de un modelo"
            elif c["pendiente_anexo_A"]:
                estado, motivo = "pendiente", "Anexo A no aprobado: no calificar todavía"
            elif tipo == "exploratoria":
                estado, motivo = "pendiente", "exploratoria: diagnóstico preliminar; no cuenta para conformidad"
            else:
                estado, motivo = "pendiente", "por calificar"
            w.writerow([
                man["corrida"], r["unidad"], r["caso"], r["variante"], r["repeticion"], r["turno"],
                c["criticidad"], c["bloque"], c["depende_de"], c["evaluacion"]["situacion"],
                r["mensaje_usuario"], r["respuesta"], c["evaluacion"]["cumple"], c["evaluacion"]["fallas"],
                "sí" if c["evaluacion"].get("comparar_variantes") else "no",
                estado, motivo, "", "", "",
            ])
            filas += 1
    return destino


def estado_breve(carpeta: Path) -> str:
    man, _, unidades, respuestas, errores = _datos(carpeta)
    ultimos: Dict[str, Dict[str, Any]] = {}
    for r in unidades:
        ultimos[r["unidad"]] = r
    plan = man["unidades_planeadas"]
    c = Counter(ultimos.get(u, {}).get("estado", "sin correr") for u in plan)
    partes = ", ".join(f"{k}: {v}" for k, v in sorted(c.items()))
    marca = {"simulacion_tecnica": " [SIMULACIÓN TÉCNICA]", "exploratoria": " [EXPLORATORIA]",
             "conformidad": " [CONFORMIDAD]"}[tipo_de(man)]
    return (f"{man['corrida']}{marca} · estado {man['estado']} · {len(plan)} unidades ({partes}) · "
            f"{len(respuestas)} respuestas registradas · {len(errores)} errores")

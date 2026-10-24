"""Calibración de la estimación de tokens con los conteos reales del modelo.

Lee respuestas.jsonl de una o varias corridas con modelo real y compara, en cada
llamada, lo que estimó el núcleo (tokens.py) con el prompt_eval_count que
devolvió Ollama. Agrupa por modelo, porque Qwen 3.5 y Qwen3 no tienen por qué
usar el mismo tokenizador.

No cambia ninguna configuración: propone un valor y la decisión queda escrita
para quien la tome.

Señales por llamada:
  subestimada         la estimación fue menor que el conteo real: el presupuesto
                      dejó de ser conservador en esa llamada.
  sin_margen          conteo real + reserva > ventana: la respuesta pudo quedarse
                      sin espacio, o Ollama pudo recortar la entrada.
  conteo_sospechoso   más de 6 caracteres por token. Con caché de prompt, algunas
                      versiones de Ollama cuentan solo lo que no estaba en caché;
                      esas llamadas no se usan para calibrar.
  sin_conteo          Ollama no devolvió prompt_eval_count.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median
from typing import Any, Dict, Iterable, List, Optional

from .tokens import calibrar
from .util import escribir_json, leer_json, leer_jsonl

MAX_CARACTERES_POR_TOKEN_CREIBLE = 6.0


def _percentil(valores: List[float], p: float) -> Optional[float]:
    if not valores:
        return None
    v = sorted(valores)
    k = max(0, min(len(v) - 1, int(math.floor(p / 100.0 * (len(v) - 1)))))
    return v[k]


def llamadas(carpeta: Path) -> List[Dict[str, Any]]:
    """Una fila por llamada al modelo, con la estimación, el conteo real y sus señales."""
    man = leer_json(carpeta / "manifiesto.json")
    nucleo = man.get("nucleo", {})
    ventana = int(nucleo.get("ventana_tokens") or 0)
    reserva = int(nucleo.get("reserva_respuesta_tokens") or 0)
    modelo = man["plataforma"]["adaptador"].get("modelo", "desconocido")
    filas = []
    for r in leer_jsonl(carpeta / "respuestas.jsonl"):
        if "unidad" not in r or r.get("simulada"):
            continue
        met = r.get("metricas") or {}
        real = met.get("prompt_eval_count")
        est = (r.get("montaje") or {}).get("total_estimado")
        car = r.get("caracteres_enviados")
        senales = []
        cpt = None
        if not real:
            senales.append("sin_conteo")
        else:
            cpt = round(car / real, 3) if car else None
            if est is not None and est < real:
                senales.append("subestimada")
            if ventana and real + reserva > ventana:
                senales.append("sin_margen")
            if cpt is not None and cpt > MAX_CARACTERES_POR_TOKEN_CREIBLE:
                senales.append("conteo_sospechoso")
        filas.append({
            "corrida": man["corrida"], "modelo": modelo, "unidad": r["unidad"], "turno": r.get("turno"),
            "caracteres_enviados": car, "tokens_estimados": est, "prompt_eval_count": real,
            "eval_count": met.get("eval_count"), "done_reason": met.get("done_reason"),
            "estado": r.get("estado"), "caracteres_por_token": cpt,
            "estimado_entre_real": round(est / real, 3) if (est and real) else None,
            "ventana": ventana, "reserva": reserva, "senales": senales,
        })
    return filas


def resumen_por_modelo(filas: Iterable[Dict[str, Any]], cpt_configurado: Optional[float] = None) -> Dict[str, Any]:
    grupos: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for f in filas:
        grupos[f["modelo"]].append(f)
    salida: Dict[str, Any] = {}
    for modelo, fs in sorted(grupos.items()):
        validas = [f for f in fs if f["prompt_eval_count"] and "conteo_sospechoso" not in f["senales"]]
        cpts = [f["caracteres_por_token"] for f in validas if f["caracteres_por_token"]]
        ratios = [f["estimado_entre_real"] for f in validas if f["estimado_entre_real"]]
        senales = Counter(s for f in fs for s in f["senales"])
        agregado = calibrar((f["caracteres_enviados"], f["prompt_eval_count"]) for f in validas)
        # Valor prudente: el percentil 5 de caracteres por token, redondeado hacia abajo a 0.1.
        p5 = _percentil(cpts, 5)
        sugerido = math.floor(p5 * 10) / 10 if p5 else None
        salida[modelo] = {
            "llamadas": len(fs),
            "llamadas_validas_para_calibrar": len(validas),
            "caracteres_por_token_agregado": agregado,
            "caracteres_por_token_min": min(cpts) if cpts else None,
            "caracteres_por_token_p5": p5,
            "caracteres_por_token_mediana": median(cpts) if cpts else None,
            "estimado_entre_real_min": min(ratios) if ratios else None,
            "estimado_entre_real_mediana": median(ratios) if ratios else None,
            "prompt_eval_count_max": max((f["prompt_eval_count"] for f in validas), default=None),
            "senales": dict(senales),
            "caracteres_por_token_configurado": cpt_configurado,
            "caracteres_por_token_sugerido": sugerido,
            "estimacion_actual_es_conservadora": (bool(ratios) and min(ratios) >= 1.0) if ratios else None,
        }
    return salida


def calibrar_corridas(carpetas: List[Path]) -> Dict[str, Any]:
    filas: List[Dict[str, Any]] = []
    cpt_conf = None
    for c in carpetas:
        filas += llamadas(c)
        est = (leer_json(c / "manifiesto.json").get("nucleo") or {}).get("estimacion") or {}
        cpt_conf = cpt_conf or est.get("caracteres_por_token")
    return {"corridas": [c.name for c in carpetas], "por_modelo": resumen_por_modelo(filas, cpt_conf), "llamadas": filas}


def texto_md(datos: Dict[str, Any]) -> str:
    L = ["# Calibración de tokens", "",
         "Compara la estimación del núcleo con el `prompt_eval_count` de Ollama. **No cambia ninguna configuración.**", "",
         f"Corridas: {', '.join(datos['corridas'])}", ""]
    if not datos["llamadas"]:
        L += ["No hay llamadas a un modelo real en estas corridas (las simulaciones técnicas no tienen conteos reales).", ""]
        return "\n".join(L) + "\n"
    for modelo, r in datos["por_modelo"].items():
        L += [f"## {modelo}", "",
              "| Medida | Valor |", "|---|---|",
              f"| Llamadas / válidas para calibrar | {r['llamadas']} / {r['llamadas_validas_para_calibrar']} |",
              f"| Caracteres por token, agregado | {r['caracteres_por_token_agregado']} |",
              f"| Caracteres por token: mínimo · p5 · mediana | {r['caracteres_por_token_min']} · {r['caracteres_por_token_p5']} · {r['caracteres_por_token_mediana']} |",
              f"| Estimado ÷ real: mínimo · mediana | {r['estimado_entre_real_min']} · {r['estimado_entre_real_mediana']} |",
              f"| Mayor prompt_eval_count | {r['prompt_eval_count_max']} |",
              f"| Señales | {', '.join(f'{k}: {v}' for k, v in r['senales'].items()) or 'ninguna'} |",
              f"| Configurado / sugerido (p5, hacia abajo) | {r['caracteres_por_token_configurado']} / {r['caracteres_por_token_sugerido']} |",
              ""]
        cons = r["estimacion_actual_es_conservadora"]
        if cons is True:
            L.append("La estimación actual fue igual o mayor que el conteo real en todas las llamadas válidas: el presupuesto fue conservador.")
        elif cons is False:
            L.append("**En alguna llamada la estimación fue menor que el conteo real.** Conviene bajar `caracteres_por_token` antes de corridas más largas.")
        if r["senales"].get("sin_margen"):
            L.append("**Hubo llamadas en las que el conteo real más la reserva superó la ventana.** Revisa si Ollama recortó la entrada (registro del servidor: «truncating»).")
        if r["senales"].get("conteo_sospechoso"):
            L.append("Algunas llamadas dieron más de 6 caracteres por token; probablemente Ollama contó solo lo que no estaba en caché. Se excluyeron.")
        L.append("")
    L += ["El cambio de `contexto.estimacion.caracteres_por_token` en las plataformas lo decide una persona y se anota en el informe de la etapa.", ""]
    return "\n".join(L) + "\n"


def escribir_calibracion(carpetas: List[Path], destino: Path) -> Dict[str, Any]:
    datos = calibrar_corridas(carpetas)
    destino.mkdir(parents=True, exist_ok=True)
    escribir_json(destino / "calibracion.json", datos)
    (destino / "calibracion.md").write_text(texto_md(datos), encoding="utf-8")
    return datos

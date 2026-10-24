"""Casos ejecutables: carga, validación, selección y unidades de trabajo.

Cada caso tiene dos partes separadas:
  - 'ejecucion': lo único que se usa para conversar con el modelo
    (mensajes de la persona y, si el guion lo pide, turnos previos de Harry
    fabricados y marcados como tales);
  - 'evaluacion': situación, conducta que cumple y fallas. Es para quien
    califica. Nunca se envía al modelo.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from .util import leer_json

ROLES = ("usuario", "harry_fabricado")
CRITICIDADES = ("crítica", "alta", "media")
FORMAS = ("un turno", "multiturno", "par")
PALABRAS_DE_RUBRICA = ("conducta que cumple", "fallas que lo delatan", "rúbrica", "criticidad")


def cargar(ruta: Path) -> Dict[str, Any]:
    return leer_json(ruta)


def _normal(t: str) -> str:
    t = t.lower()
    t = re.sub(r"[«»\"“”'¿?¡!.,;:()]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def turnos_para_envio(caso: Dict[str, Any], variante: str) -> List[Dict[str, Any]]:
    """Copia de los turnos de una variante: solo rol, texto y si se evalúa."""
    return [
        {"rol": t["rol"], "texto": t["texto"], "evaluar": bool(t.get("evaluar"))}
        for t in caso["ejecucion"]["variantes"][variante]
    ]


def validar(datos: Dict[str, Any], ids_esperados: Optional[Set[str]] = None) -> List[str]:
    problemas: List[str] = []
    casos = datos.get("casos", [])
    ids = [c.get("id") for c in casos]
    repetidos = sorted({i for i in ids if ids.count(i) > 1})
    if repetidos:
        problemas.append(f"IDs repetidos: {repetidos}")
    if ids_esperados is not None:
        faltan = sorted(ids_esperados - set(ids))
        sobran = sorted(set(ids) - ids_esperados)
        if faltan:
            problemas.append(f"Faltan casos del generador: {faltan}")
        if sobran:
            problemas.append(f"Casos que no están en el generador: {sobran}")

    for c in casos:
        cid = c.get("id", "?")
        for clave in ("bloque", "criticidad", "forma", "etiquetas", "origen", "depende_de",
                      "pendiente_anexo_A", "ejecucion", "evaluacion"):
            if clave not in c:
                problemas.append(f"{cid}: falta '{clave}'")
        if c.get("criticidad") not in CRITICIDADES:
            problemas.append(f"{cid}: criticidad inválida {c.get('criticidad')!r}")
        if c.get("forma") not in FORMAS:
            problemas.append(f"{cid}: forma inválida {c.get('forma')!r}")
        dep_anexo = "Anexo A" in c.get("depende_de", "")
        if bool(c.get("pendiente_anexo_A")) != dep_anexo:
            problemas.append(f"{cid}: 'pendiente_anexo_A' no coincide con 'depende_de'")

        variantes = (c.get("ejecucion") or {}).get("variantes") or {}
        if not variantes:
            problemas.append(f"{cid}: sin variantes ejecutables")
            continue
        if c.get("forma") == "par" and len(variantes) != 2:
            problemas.append(f"{cid}: un par debe tener exactamente 2 variantes")
        if c.get("forma") != "par" and len(variantes) != 1:
            problemas.append(f"{cid}: un caso que no es par debe tener 1 variante")

        ev = c.get("evaluacion") or {}
        frases_rubrica = [
            _normal(f) for campo in ("cumple", "fallas")
            for f in str(ev.get(campo, "")).split(";") if len(_normal(f)) >= 15
        ]
        for nombre, turnos in variantes.items():
            if not turnos:
                problemas.append(f"{cid}/{nombre}: variante vacía")
                continue
            if turnos[0].get("rol") != "usuario":
                problemas.append(f"{cid}/{nombre}: debe empezar con la persona")
            if turnos[-1].get("rol") != "usuario":
                problemas.append(f"{cid}/{nombre}: debe terminar con la persona")
            if not any(t.get("evaluar") for t in turnos if t.get("rol") == "usuario"):
                problemas.append(f"{cid}/{nombre}: ningún turno marcado para evaluar")
            for i, t in enumerate(turnos):
                if t.get("rol") not in ROLES:
                    problemas.append(f"{cid}/{nombre}[{i}]: rol inválido {t.get('rol')!r}")
                if not str(t.get("texto", "")).strip():
                    problemas.append(f"{cid}/{nombre}[{i}]: texto vacío")
                if t.get("rol") == "harry_fabricado":
                    if i == 0 or turnos[i - 1].get("rol") != "usuario":
                        problemas.append(f"{cid}/{nombre}[{i}]: turno fabricado sin mensaje previo de la persona")
                    if t.get("evaluar"):
                        problemas.append(f"{cid}/{nombre}[{i}]: un turno fabricado no se evalúa")
                texto_n = _normal(str(t.get("texto", "")))
                for palabra in PALABRAS_DE_RUBRICA:
                    if palabra in texto_n:
                        problemas.append(f"{cid}/{nombre}[{i}]: el mensaje contiene '{palabra}'")
                for frase in frases_rubrica:
                    if frase in texto_n:
                        problemas.append(f"{cid}/{nombre}[{i}]: el mensaje filtra la rúbrica: «{frase[:40]}…»")
    return problemas


def seleccionar(
    casos: List[Dict[str, Any]],
    ids: Optional[Iterable[str]] = None,
    bloques: Optional[Iterable[str]] = None,
    criticidades: Optional[Iterable[str]] = None,
    formas: Optional[Iterable[str]] = None,
    incluir_anexo_a: bool = False,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Devuelve (seleccionados, excluidos_por_anexo_A)."""
    ids_s = set(ids) if ids else None
    if ids_s:
        desconocidos = ids_s - {c["id"] for c in casos}
        if desconocidos:
            raise ValueError(f"IDs desconocidos: {sorted(desconocidos)}")
    sel, excluidos = [], []
    for c in casos:
        if ids_s is not None and c["id"] not in ids_s:
            continue
        if bloques and c["bloque"] not in set(bloques):
            continue
        if criticidades and c["criticidad"] not in set(criticidades):
            continue
        if formas and c["forma"] not in set(formas):
            continue
        if c["pendiente_anexo_A"] and not incluir_anexo_a:
            excluidos.append(c["id"])
            continue
        sel.append(c)
    return sel, excluidos


def unidades(seleccion: List[Dict[str, Any]], repeticiones: int) -> List[Dict[str, Any]]:
    """Unidad = un caso, una variante, una repetición. Orden estable."""
    salida = []
    for c in seleccion:
        for variante in sorted(c["ejecucion"]["variantes"]):
            for r in range(1, repeticiones + 1):
                salida.append({
                    "unidad": f"{c['id']}|{variante}|r{r}",
                    "caso": c["id"],
                    "variante": variante,
                    "repeticion": r,
                })
    return salida

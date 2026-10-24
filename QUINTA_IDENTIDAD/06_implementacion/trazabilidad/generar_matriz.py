"""Valida la matriz de trazabilidad y genera matriz.md y matriz.csv.

Las anclas I-xx se leen de las instrucciones que usan las plataformas
(configuracion/plataformas/*.json). Todas deben usar el mismo archivo; si no,
la matriz no se genera. Las matrices de versiones anteriores de las
instrucciones se conservan en trazabilidad/versiones/.

Uso:  python3 -I trazabilidad/generar_matriz.py   (desde 06_implementacion)
"""

from __future__ import annotations

import csv
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

IMPL = Path(__file__).resolve().parents[1]


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def instrucciones_en_uso():
    """(ruta, versión) de las instrucciones que usan todas las plataformas, o los problemas."""
    usadas = {}
    for p in sorted((IMPL / "configuracion" / "plataformas").glob("*.json")):
        usadas[p.stem] = json.loads(p.read_text(encoding="utf-8"))["instrucciones"].replace("${IMPL}", str(IMPL))
    distintas = sorted(set(usadas.values()))
    if len(distintas) != 1:
        return None, None, [f"Las plataformas no usan las mismas instrucciones: {usadas}"]
    ruta = Path(distintas[0])
    if not ruta.exists():
        return None, None, [f"No existen las instrucciones en uso: {ruta}"]
    m = re.search(r"^version:\s*(\S+)", ruta.read_text(encoding="utf-8"), re.MULTILINE)
    return ruta, (m.group(1) if m else "sin versión"), []


def problemas_de_matriz():
    req = _cargar("requisitos", IMPL / "trazabilidad" / "requisitos.py")
    ruta, _, problemas = instrucciones_en_uso()
    if problemas:
        return req, problemas
    instr = ruta.read_text(encoding="utf-8")
    anclas = set(re.findall(r"<!--\s*(I-\d+)", instr))
    casos = {c["id"] for c in json.loads((IMPL / "casos" / "casos_ejecutables.json").read_text(encoding="utf-8"))["casos"]}
    problemas, usadas = [], set()
    ids = [r[0] for r in req.REQUISITOS]
    for i, n in Counter(ids).items():
        if n > 1:
            problemas.append(f"ID de requisito repetido: {i}")
    for rid, fuente, texto, impl, cs, estado, verif in req.REQUISITOS:
        if estado not in req.ESTADOS:
            problemas.append(f"{rid}: estado desconocido {estado}")
        if verif not in req.VERIFICACION:
            problemas.append(f"{rid}: verificación desconocida {verif}")
        for x in impl:
            if x.startswith("I-"):
                if x not in anclas:
                    problemas.append(f"{rid}: la instrucción {x} no existe en el borrador")
                usadas.add(x)
        for c in cs:
            if c not in casos:
                problemas.append(f"{rid}: el caso {c} no existe")
    for a in sorted(anclas - usadas):
        problemas.append(f"La instrucción {a} no está asociada a ningún requisito")
    return req, problemas


def main() -> int:
    req, problemas = problemas_de_matriz()
    if problemas:
        print("ERROR:")
        for p in problemas:
            print("  -", p)
        return 1
    filas = req.REQUISITOS
    ruta, version, _ = instrucciones_en_uso()
    rel = ruta.relative_to(IMPL).as_posix()
    with open(IMPL / "trazabilidad" / "matriz.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "fuente", "requisito", "implementacion", "casos", "estado", "estado_descripcion", "verificacion"])
        for rid, fuente, texto, impl, cs, estado, verif in filas:
            w.writerow([rid, fuente, texto, "; ".join(impl), "; ".join(cs), estado, req.ESTADOS[estado], req.VERIFICACION[verif]])
    cuenta = Counter(r[5] for r in filas)
    L = ["# Matriz de trazabilidad de Harry", "",
         "Generada por `trazabilidad/generar_matriz.py` desde `requisitos.py`, que es su fuente única. "
         f"Se llama a cada instrucción por su ancla (`I-01` a `I-17`) en `{rel}` (borrador {version}), "
         "que es el archivo que usan todas las plataformas. Los componentes de código se marcan con `c:`. "
         "Las matrices de versiones anteriores de las instrucciones están en `trazabilidad/versiones/`.", "",
         "## Estados", "", "| Estado | Significado | Requisitos |", "|---|---|---|"]
    for clave, desc in req.ESTADOS.items():
        L.append(f"| `{clave}` | {desc} | {cuenta.get(clave, 0)} |")
    L += ["", f"**Total: {len(filas)} requisitos.**", "",
          "## Matriz", "", "| Id | Fuente | Requisito | Implementación | Casos | Estado | Verificación |", "|---|---|---|---|---|---|---|"]
    for rid, fuente, texto, impl, cs, estado, verif in filas:
        L.append(f"| {rid} | {fuente} | {texto} | {', '.join(impl) or '—'} | {', '.join(cs) or '—'} | `{estado}` | {req.VERIFICACION[verif]} |")
    (IMPL / "trazabilidad" / "matriz.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"OK: {len(filas)} requisitos -> trazabilidad/matriz.md y matriz.csv")
    print("    " + ", ".join(f"{k}: {v}" for k, v in cuenta.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())

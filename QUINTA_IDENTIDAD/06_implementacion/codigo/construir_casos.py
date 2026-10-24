"""Construye casos/casos_ejecutables.json.

Une dos fuentes sin modificarlas:
  - 05_pruebas/_generador/generar.py  (IDs, criticidad, rúbricas, procedencia)
  - 06_implementacion/casos/guiones.py (mensajes concretos)

Uso:  python3 -I construir_casos.py
Sale con error si falta o sobra algún guion, o si la validación encuentra problemas.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from harry_nucleo import NUCLEO_VERSION, rutas  # noqa: E402
from harry_nucleo.casos import validar  # noqa: E402
from harry_nucleo.util import ahora_iso, escribir_json, sha256_archivo  # noqa: E402


def cargar_modulo(nombre: str, ruta: Path):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # no ejecuta main(): __name__ no es "__main__"
    return mod


def normalizar_guion(valor):
    """Devuelve (variantes: dict, nota: str)."""
    if isinstance(valor, list):
        variantes, nota = {"unica": valor}, ""
    elif "variantes" in valor:
        variantes, nota = valor["variantes"], valor.get("nota", "")
    else:
        variantes, nota = {"unica": valor["turnos"]}, valor.get("nota", "")
    salida = {}
    for nombre, turnos in variantes.items():
        turnos = [dict(t) for t in turnos]
        if not any(t.get("evaluar") for t in turnos):
            for t in reversed(turnos):
                if t["rol"] == "usuario":
                    t["evaluar"] = True
                    break
        for t in turnos:
            t["evaluar"] = bool(t.get("evaluar"))
        salida[nombre] = turnos
    return salida, nota


def main() -> int:
    gen_ruta = rutas.raiz() / "05_pruebas" / "_generador" / "generar.py"
    gui_ruta = rutas.impl() / "casos" / "guiones.py"
    gen = cargar_modulo("generador_05", gen_ruta)
    gui = cargar_modulo("guiones_06", gui_ruta)

    ids_gen = [c[0] for c in gen.CASOS]
    faltan = [i for i in ids_gen if i not in gui.GUIONES]
    sobran = [i for i in gui.GUIONES if i not in ids_gen]
    if faltan or sobran:
        print(f"ERROR: guiones que faltan: {faltan}; guiones sin caso: {sobran}")
        return 1

    casos = []
    for (cid, bloque, etiquetas, crit, forma, situacion, cumple, fallas, depende, origen) in gen.CASOS:
        variantes, nota = normalizar_guion(gui.GUIONES[cid])
        casos.append({
            "id": cid,
            "bloque": bloque,
            "bloque_nombre": gen.BLOQUES[bloque],
            "criticidad": crit,
            "forma": forma,
            "etiquetas": etiquetas.split("; "),
            "origen": origen,
            "depende_de": depende,
            "pendiente_anexo_A": "Anexo A" in depende,
            "depende_de_plataforma": "plataforma" in depende,
            "ejecucion": {"variantes": variantes, "nota": nota},
            "evaluacion": {
                "situacion": situacion,
                "cumple": cumple,
                "fallas": fallas,
                "comparar_variantes": forma == "par",
            },
        })

    datos = {
        "meta": {
            "descripcion": "Casos ejecutables de Harry. 'ejecucion' se envía al modelo; 'evaluacion' nunca.",
            "generado": ahora_iso(),
            "nucleo_version": NUCLEO_VERSION,
            "hash_generador_05": sha256_archivo(gen_ruta),
            "hash_guiones": sha256_archivo(gui_ruta),
            "total": len(casos),
        },
        "casos": casos,
    }
    problemas = validar(datos, set(ids_gen))
    if problemas:
        print("ERROR de validación:")
        for p in problemas:
            print("  -", p)
        return 1
    destino = rutas.impl() / "casos" / "casos_ejecutables.json"
    escribir_json(destino, datos)
    formas = {}
    for c in casos:
        formas[c["forma"]] = formas.get(c["forma"], 0) + 1
    pend = sum(c["pendiente_anexo_A"] for c in casos)
    print(f"OK: {len(casos)} casos -> {destino}")
    print(f"    formas: {formas} | pendientes del Anexo A: {pend}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

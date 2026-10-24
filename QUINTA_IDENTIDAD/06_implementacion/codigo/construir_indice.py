"""Construye recuperacion/indice.json a partir de configuracion/corpus.json.

Uso:  python3 -I construir_indice.py
Falla si el corpus incluye algún archivo excluido (pruebas, revisiones con
rúbricas, resultados) o si falta una fuente.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))

from harry_nucleo import NUCLEO_VERSION, rutas  # noqa: E402
from harry_nucleo.recuperacion import ErrorIndice, cargar_corpus, construir_indice  # noqa: E402
from harry_nucleo.util import ahora_iso, escribir_json, sha256_archivo  # noqa: E402


def main() -> int:
    corpus = cargar_corpus()
    try:
        indice = construir_indice(corpus)
    except ErrorIndice as e:
        print(f"ERROR: {e}")
        return 1
    indice["meta"] = {
        "construido": ahora_iso(),
        "nucleo_version": NUCLEO_VERSION,
        "hash_corpus": sha256_archivo(rutas.impl() / "configuracion" / "corpus.json"),
        "fragmentos": len(indice["fragmentos"]),
    }
    destino = rutas.impl() / "recuperacion" / "indice.json"
    escribir_json(destino, indice)
    por_cat = Counter(f["categoria"] for f in indice["fragmentos"])
    print(f"OK: {len(indice['fragmentos'])} fragmentos de {len(indice['fuentes'])} fuentes -> {destino}")
    print(f"    por categoría: {dict(por_cat)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

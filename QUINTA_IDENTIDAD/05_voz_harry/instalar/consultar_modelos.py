"""Consulta en Hugging Face los tamaños y licencias de los pesos que usaría cada motor. NO descarga nada.

Uso:  python3 -I instalar/consultar_modelos.py [--motor piper|kokoro|chatterbox] [--variante v2|v3|es-mx-latam]

Solo hace peticiones GET a la API pública de metadatos (huggingface.co/api/...).
Guarda lo consultado en evaluacion/registros/consulta_modelos_<fecha>.json.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from datetime import datetime
from pathlib import Path

VOZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VOZ))

from voz_harry import catalogo  # noqa: E402

API = "https://huggingface.co/api/models"


def _get(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": "voz-harry/0.1 (consulta de metadatos)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def info_repo(repo: str):
    d = _get(f"{API}/{repo}")
    card = d.get("cardData") or {}
    return {"repo": repo, "sha": d.get("sha"), "licencia": card.get("license") or d.get("license"),
            "gated": d.get("gated"), "ultima_modificacion": d.get("lastModified")}


def arbol(repo: str, revision: str = "main", ruta: str = ""):
    url = f"{API}/{repo}/tree/{revision}" + (f"/{ruta}" if ruta else "") + "?recursive=1"
    return {e["path"]: {"tamano": e.get("size"), "sha256": (e.get("lfs") or {}).get("oid")}
            for e in _get(url) if e.get("type") == "file"}


def archivos_de(motor: str, variante: str = "v2"):
    cat = catalogo.cargar()
    m = cat["motores"][motor]
    if motor == "piper":
        voces = [v for v in cat["voces"] if v["motor"] == "piper"]
        rutas_ = [a for v in voces for a in v.get("archivos", [])]
        return m["repo_pesos"], m["revision_pesos"], rutas_
    if motor == "kokoro":
        voces = sorted({v["id"] for v in cat["voces"] if v["motor"] == "kokoro" and "," not in v["id"]})
        return m["repo_pesos"], "main", m["archivos_base"] + [f"voices/{v}.pt" for v in voces]
    if motor == "chatterbox":
        if variante == "es-mx-latam":
            return "ResembleAI/Chatterbox-Multilingual-es-mx-latam", "main", None  # todos: la lista exacta está por verificar
        base = list(m["archivos_base_v2"])
        if variante == "v3":
            base = [m["archivo_v3"] if a.startswith("t3_mtl23ls_") else a for a in base]
        return m["repo_pesos"], "main", base
    raise SystemExit(f"Motor sin pesos que consultar: {motor}")


def consultar(motor: str, variante: str = "v2"):
    repo, revision, quiero = archivos_de(motor, variante)
    inf = info_repo(repo)
    todos = arbol(repo, revision)
    if quiero is None:
        quiero = sorted(todos)
    filas = [{"ruta": r, **todos.get(r, {"tamano": None, "sha256": None}), "existe": r in todos} for r in quiero]
    total = sum(f["tamano"] or 0 for f in filas)
    return {"motor": motor, "variante": variante, "repo": repo, "revision": revision, **inf,
            "archivos": filas, "total_bytes": total, "consultado": datetime.now().isoformat(timespec="seconds")}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--motor", choices=["piper", "kokoro", "chatterbox"])
    ap.add_argument("--variante", default="v2", choices=["v2", "v3", "es-mx-latam"])
    a = ap.parse_args()
    motores = [a.motor] if a.motor else ["piper", "kokoro", "chatterbox"]
    resultados = []
    for m in motores:
        try:
            r = consultar(m, a.variante)
        except Exception as e:
            print(f"== {m}: no se pudo consultar ({e})")
            continue
        resultados.append(r)
        print(f"== {m} · {r['repo']}@{r['revision']} · licencia declarada: {r['licencia']} · acceso restringido: {r['gated']}")
        for f in r["archivos"]:
            tam = f"{f['tamano'] / 1e6:8.1f} MB" if f["tamano"] else "   ¿?     "
            print(f"   {tam}  {f['ruta']}{'' if f['existe'] else '   (NO EXISTE en el repositorio)'}")
        print(f"   Total: {r['total_bytes'] / 1e6:.1f} MB")
    destino = VOZ / "evaluacion" / "registros" / f"consulta_modelos_{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nNada se descargó. Consulta guardada en {destino}")
    print("Las voces de Piper tienen además su licencia en cada MODEL_CARD; descargar_modelos.py la guarda junto a la voz.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

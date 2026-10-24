"""Descarga los pesos de un motor a 05_voz_harry/modelos/, SOLO con autorización expresa.

Uso:
  python3 -I instalar/descargar_modelos.py --motor piper --voz es_MX-claude-high --voz en_GB-alan-medium --autorizo
  python3 -I instalar/descargar_modelos.py --motor kokoro --autorizo
  python3 -I instalar/descargar_modelos.py --motor chatterbox --variante v2 --autorizo --autorizo-grande

Antes de descargar, consulta y muestra tamaños y licencia, y pide escribir «sí» (salvo --si).
- Piper: archivos a modelos/piper/ (.onnx, .onnx.json y la MODEL_CARD con su licencia),
  con verificación SHA-256 del .onnx contra Hugging Face.
- Kokoro y Chatterbox: a la caché de Hugging Face del proyecto (modelos/hf), con el
  huggingface_hub del entorno del motor. Si ya tienes esos pesos en otra caché,
  apunta HF_HOME a ella en lugar de descargarlos otra vez.
Chatterbox exige además --autorizo-grande (varios GB).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path

VOZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VOZ))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from consultar_modelos import consultar  # noqa: E402
from voz_harry import catalogo, rutas  # noqa: E402


def archivos_piper(voces):
    por_id = {v["id"]: v for v in catalogo.cargar()["voces"] if v["motor"] == "piper"}
    desconocidas = [v for v in voces if v not in por_id]
    if desconocidas:
        raise SystemExit(f"Voces de Piper que no están en configuracion/catalogo.json: {desconocidas}")
    return {v: por_id[v]["archivos"] for v in voces}


def _descargar(url: str, destino: Path, sha256: str = None) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(destino.suffix + ".parcial")
    h = hashlib.sha256()
    req = urllib.request.Request(url, headers={"User-Agent": "voz-harry/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r, open(tmp, "wb") as f:
        while True:
            bloque = r.read(1 << 20)
            if not bloque:
                break
            f.write(bloque)
            h.update(bloque)
    if sha256 and h.hexdigest() != sha256:
        tmp.unlink()
        raise SystemExit(f"SHA-256 distinto en {destino.name}: se descartó la descarga")
    tmp.replace(destino)


def piper(voces, info) -> None:
    carpeta = rutas.modelos() / "piper"
    por_ruta = {f["ruta"]: f for f in info["archivos"]}
    for voz, rutas_voz in archivos_piper(voces).items():
        for r in rutas_voz:
            nombre = f"{voz}.MODEL_CARD.md" if r.endswith("MODEL_CARD") else Path(r).name
            url = f"https://huggingface.co/{info['repo']}/resolve/{info['revision']}/{r}"
            print(f"  descargando {r} → modelos/piper/{nombre}")
            _descargar(url, carpeta / nombre, por_ruta[r].get("sha256") if r.endswith(".onnx") else None)


def con_hf_hub(motor: str, info) -> None:
    python = rutas.python_de(motor)
    if not python.exists():
        raise SystemExit(f"Primero crea el entorno: bash instalar/crear_entornos.sh {motor}")
    patrones = [f["ruta"] for f in info["archivos"]]
    codigo = ("import sys, json; from huggingface_hub import snapshot_download; "
              "print(snapshot_download(repo_id=sys.argv[1], revision=sys.argv[2], allow_patterns=json.loads(sys.argv[3])))")
    env = dict(os.environ, HF_HOME=str(rutas.cache_hf()), HF_HUB_OFFLINE="0")
    subprocess.run([str(python), "-I", "-c", codigo, info["repo"], info.get("sha") or "main", json.dumps(patrones)],
                   check=True, env=env)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--motor", required=True, choices=["piper", "kokoro", "chatterbox"])
    ap.add_argument("--voz", action="append", help="Piper: id de la voz (se puede repetir)")
    ap.add_argument("--variante", default="v2", choices=["v2", "v3", "es-mx-latam"])
    ap.add_argument("--autorizo", action="store_true", help="Autorizo la descarga")
    ap.add_argument("--autorizo-grande", action="store_true", help="Autorizo una descarga de varios GB (Chatterbox)")
    ap.add_argument("--si", action="store_true", help="No preguntar")
    a = ap.parse_args()
    if not a.autorizo:
        print("Falta --autorizo. Nada se descarga sin autorización expresa.")
        return 3
    if a.motor == "chatterbox" and not a.autorizo_grande:
        print("Chatterbox pesa varios GB: falta --autorizo-grande.")
        return 3
    if a.motor == "piper" and not a.voz:
        print("Indica al menos una voz con --voz (ver configuracion/catalogo.json).")
        return 2
    info = consultar(a.motor, a.variante)
    if a.motor == "piper":
        quiero = {r for rs in archivos_piper(a.voz).values() for r in rs}
        sel = [f for f in info["archivos"] if f["ruta"] in quiero]
        info = dict(info, archivos=sel, total_bytes=sum(f["tamano"] or 0 for f in sel))
    faltan = [f["ruta"] for f in info["archivos"] if not f["existe"]]
    if faltan:
        print(f"No existen en el repositorio: {faltan}. Revisa el catálogo antes de seguir.")
        return 1
    print(f"{info['repo']}@{info['revision']} · licencia declarada: {info['licencia']}")
    for f in info["archivos"]:
        print(f"   {(f['tamano'] or 0) / 1e6:8.1f} MB  {f['ruta']}")
    print(f"   Total: {info['total_bytes'] / 1e6:.1f} MB → {rutas.modelos()}")
    if not a.si and input("¿Descargar? Escribe «sí»: ").strip().lower() not in ("sí", "si"):
        print("Cancelado; nada se descargó.")
        return 0
    if a.motor == "piper":
        piper(a.voz, info)
    else:
        con_hf_hub(a.motor, info)
    print("Descarga terminada. Comprueba sin conexión con: python3 -I voz.py muestra --motor "
          f"{a.motor} --voz <voz> (el trabajador corre con HF_HUB_OFFLINE=1)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

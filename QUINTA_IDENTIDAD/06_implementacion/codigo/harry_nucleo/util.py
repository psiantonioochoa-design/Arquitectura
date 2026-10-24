"""Utilidades de archivo: hashes, JSON atómico y JSONL con escritura segura."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Iterator


def ahora_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def sha256_bytes(datos: bytes) -> str:
    return hashlib.sha256(datos).hexdigest()


def sha256_texto(texto: str) -> str:
    return sha256_bytes(texto.encode("utf-8"))


def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def sha256_codigo(carpeta: Path) -> str:
    """Huella de todos los .py de una carpeta, en orden estable."""
    h = hashlib.sha256()
    for p in sorted(carpeta.rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        h.update(str(p.relative_to(carpeta)).encode("utf-8"))
        h.update(p.read_bytes())
    return h.hexdigest()


def escribir_json(ruta: Path, datos: Any) -> None:
    """Escritura atómica: archivo temporal en la misma carpeta y renombrado."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(ruta.parent), prefix=".tmp_", suffix=".json")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, ruta)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def leer_json(ruta: Path) -> Any:
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def anexar_jsonl(ruta: Path, registro: dict) -> None:
    """Añade una línea y la fuerza a disco antes de seguir."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def leer_jsonl(ruta: Path) -> Iterator[dict]:
    if not ruta.exists():
        return
    with open(ruta, encoding="utf-8") as f:
        for n, linea in enumerate(f, 1):
            linea = linea.strip()
            if not linea:
                continue
            try:
                yield json.loads(linea)
            except json.JSONDecodeError:
                # Una línea cortada por un corte de energía no invalida las demás.
                yield {"_linea_danada": n}


def unir(items: Iterable[str]) -> str:
    return ", ".join(items)

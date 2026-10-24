"""Catálogo de motores y voces, textos de prueba y nombres de archivo. Solo biblioteca estándar."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from . import rutas


def cargar() -> Dict[str, Any]:
    return json.loads((rutas.configuracion() / "catalogo.json").read_text(encoding="utf-8"))


def textos() -> List[Dict[str, str]]:
    return json.loads((rutas.configuracion() / "textos_prueba.json").read_text(encoding="utf-8"))["textos"]


def voces(motor: Optional[str] = None, incluir_experimentales: bool = True,
          incluir_pruebas: bool = False) -> List[Dict[str, Any]]:
    salida = []
    for v in cargar()["voces"]:
        if motor and v["motor"] != motor:
            continue
        if v.get("experimental") and not incluir_experimentales:
            continue
        if v.get("prueba_de_tuberia") and not incluir_pruebas:
            continue
        salida.append(v)
    return salida


def combinaciones(lista_voces: List[Dict[str, Any]], ids_textos: Optional[List[str]] = None):
    """(voz, texto) solo donde el idioma del texto está entre los de la voz."""
    for v in lista_voces:
        for t in textos():
            if ids_textos and t["id"] not in ids_textos:
                continue
            if t["idioma"] in v["idiomas"]:
                yield v, t


def slug(texto: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", texto).strip("-") or "x"


def clave_voz(v: Dict[str, Any]) -> str:
    return slug(v["id"] + (f"-{v['variante']}" if v.get("variante") else ""))


def nombre_muestra(motor: str, voz: Dict[str, Any], idioma: str, prueba: str) -> str:
    """motor__voz__idioma__prueba.wav, p. ej. kokoro__bm_george__en__06.wav"""
    return f"{slug(motor)}__{clave_voz(voz)}__{slug(idioma)}__{slug(prueba)}.wav"

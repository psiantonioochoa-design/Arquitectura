"""Diagnóstico de una plataforma.

Por defecto es estático: revisa archivos, manifiestos de modelos y memoria.
No inicia Ollama, no carga modelos y no conversa. Con consultar_servidor=True
hace solo consultas GET que tampoco cargan modelos (/api/version, /api/tags, /api/ps).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

from . import rutas
from .casos import cargar, validar
from .nucleo import Nucleo

OK, AVISO, ERROR = "OK", "AVISO", "ERROR"


def _manifiesto_modelo(almacen: Path, nombre_manifiesto: str) -> List[Tuple[str, str]]:
    salida: List[Tuple[str, str]] = []
    m = almacen / "manifests" / nombre_manifiesto
    if not m.exists():
        return [(ERROR, f"No existe el manifiesto del modelo: {m}")]
    try:
        datos = json.loads(m.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return [(ERROR, f"Manifiesto ilegible {m}: {e}")]
    capas = datos.get("layers", [])
    total = 0
    faltan = 0
    for capa in capas:
        blob = almacen / "blobs" / capa["digest"].replace(":", "-")
        if not blob.exists():
            faltan += 1
            salida.append((ERROR, f"Falta la capa {capa['digest'][:19]}… ({capa.get('mediaType')})"))
        elif blob.stat().st_size != capa.get("size"):
            faltan += 1
            salida.append((ERROR, f"Tamaño distinto en {capa['digest'][:19]}…"))
        else:
            total += capa.get("size", 0)
    if not faltan:
        salida.append((OK, f"Manifiesto {nombre_manifiesto}: {len(capas)} capas presentes, {total / 1e9:.2f} GB "
                           "(tamaños comprobados; hashes de pesos no recalculados)"))
    return salida


def diagnosticar(plataforma: Dict[str, Any], proyecto: Dict[str, Any], consultar_servidor: bool = False) -> List[Tuple[str, str]]:
    r: List[Tuple[str, str]] = []
    r.append((OK, f"Raíz del proyecto: {rutas.raiz()}"))
    for clave, valor in proyecto["documentos_vigilados"].items():
        p = rutas.ruta(valor)
        r.append((OK if p.exists() else ERROR, f"{clave}: {p}"))

    p_casos = rutas.ruta(proyecto["casos_ejecutables"])
    if p_casos.exists():
        datos = cargar(p_casos)
        problemas = validar(datos)
        if problemas:
            r.append((ERROR, f"Casos ejecutables con {len(problemas)} problemas (corre `validar`)"))
        else:
            n = len(datos["casos"])
            pend = sum(c["pendiente_anexo_A"] for c in datos["casos"])
            r.append((OK, f"Casos ejecutables: {n} válidos ({pend} pendientes del Anexo A)"))
    else:
        r.append((ERROR, f"No existen los casos ejecutables: {p_casos} (corre construir_casos.py)"))

    try:
        nucleo = Nucleo(plataforma, verificar_indice=False)
        nivel = OK if nucleo.estado_instrucciones in ("simulacion", "borrador", "aprobado") else AVISO
        r.append((nivel, f"Instrucciones: «{nucleo.estado_instrucciones}» v{nucleo.version_instrucciones} "
                         f"({nucleo.ruta_instrucciones.name}), ~{nucleo.tokens_mensaje(nucleo.instrucciones)} tokens estimados "
                         f"de una ventana de {nucleo.ventana} con {nucleo.reserva} reservados para la respuesta"))
        if nucleo.estado_instrucciones != "aprobado":
            r.append((AVISO, "Instrucciones no aprobadas por el custodio: solo sirven para corridas exploratorias"))
        if nucleo.bloque_recursos:
            r.append((OK, f"Registro de recursos de ayuda: {len(nucleo.recursos_enviados)} verificados se envían como datos "
                          f"(~{nucleo.tokens_mensaje(nucleo.bloque_recursos)} tokens estimados)"))
        from .util import leer_json
        declarada = str((leer_json(rutas.ruta(proyecto["aprobaciones"])).get("instrucciones_operativas") or {}).get("version", ""))
        if nucleo.version_instrucciones not in declarada.split():
            r.append((AVISO, f"aprobaciones.json registra las instrucciones como «{declarada}», pero esta plataforma usa la "
                             f"versión {nucleo.version_instrucciones}. Solo el custodio edita ese archivo."))
    except Exception as e:  # noqa: BLE001
        r.append((ERROR, f"Instrucciones: {e}"))
    rec = plataforma.get("recuperacion") or {}
    if rec.get("activa"):
        from .recuperacion import ErrorIndice, Recuperador
        try:
            rr = Recuperador(rutas.ruta(rec["indice"]), rec.get("categorias", []))
            r.append((OK, f"Índice documental al día: {len(rr.fragmentos)} fragmentos enviables "
                          f"({', '.join(rr.categorias)}); el Anexo A y las versiones archivadas no se envían"))
        except ErrorIndice as e:
            r.append((ERROR, f"Índice documental: {e}"))
    else:
        r.append((AVISO, "Recuperación documental desactivada en esta plataforma"))

    cfg = plataforma["adaptador"]
    if cfg["tipo"] == "simulacion":
        r.append((OK, "Adaptador de simulación técnica: no usa modelo ni red."))
        return r

    ejecutable = Path(cfg.get("ejecutable_ollama", ""))
    if ejecutable.exists() and os.access(ejecutable, os.X_OK):
        r.append((OK, f"Ejecutable de Ollama presente: {ejecutable} (no se inicia)"))
    else:
        r.append((ERROR, f"No encuentro el ejecutable de Ollama: {ejecutable}"))
    almacen = Path(cfg.get("almacen_modelos", ""))
    if almacen.exists():
        r.append((OK, f"Almacén de modelos: {almacen} (se referencia, no se copia)"))
        if cfg.get("manifiesto"):
            r.extend(_manifiesto_modelo(almacen, cfg["manifiesto"]))
    else:
        r.append((ERROR, f"No existe el almacén de modelos: {almacen}"))

    from .adaptadores.ollama import AdaptadorOllama, memoria_libre_porcentaje
    mem = memoria_libre_porcentaje()
    minimo = cfg.get("memoria_libre_minima_porcentaje")
    if mem is None:
        r.append((AVISO, "Memoria disponible: desconocida (la corrida real no empezaría)"))
    else:
        nivel = OK if (minimo is None or mem >= minimo) else AVISO
        r.append((nivel, f"Memoria disponible según macOS: {mem}% (mínimo configurado: {minimo}%)"))
    r.append((AVISO if not cfg.get("permitir_conversaciones_reales") else OK,
              f"permitir_conversaciones_reales = {cfg.get('permitir_conversaciones_reales')}"))

    adaptador = AdaptadorOllama(cfg)
    if consultar_servidor:
        from .adaptadores.base import ErrorAdaptador
        try:
            r.append((OK, f"Servidor Ollama {adaptador.host}: versión {adaptador.version()}"))
            nombres = [m.get("name") for m in adaptador.modelos_instalados()]
            r.append((OK if cfg["modelo"] in nombres else ERROR, f"Modelos que ve el servidor: {', '.join(nombres)}"))
            cargados = [m.get("name") for m in adaptador.modelos_cargados()]
            r.append((OK, f"Modelos cargados ahora: {', '.join(cargados) or 'ninguno'}"))
        except ErrorAdaptador as e:
            r.append((AVISO, str(e)))
    else:
        r.append((OK, "Servidor no consultado (usa --consultar-servidor; solo hace GET y no carga modelos)."))
        r.append((OK, f"Comando manual para iniciarlo, si algún día se autoriza: {adaptador.comando_manual()}"))
    return r

"""Línea de órdenes de la voz de Harry. Solo biblioteca estándar (sirve el Python 3.9 del sistema).

  equipo       describe el equipo real (etiqueta de las muestras)
  motores      estado de entornos y modelos en disco; no descarga nada
  muestra      genera UNA muestra real y la comprueba (primer paso con cada motor)
  generar      genera las muestras de comparación (los 6 textos en las combinaciones compatibles)
  interfaz     abre la interfaz local en 127.0.0.1
  informe      escribe evaluacion/comparacion_<equipo>.md (medidas objetivas y valoración auditiva, por separado)
"""

from __future__ import annotations

import argparse
import json
from typing import List, Optional

from . import catalogo, equipo, rutas
from .cliente import ClienteMotor, ErrorCliente, entorno_listo


def _lista(v: Optional[str]) -> Optional[List[str]]:
    return [x.strip() for x in v.split(",") if x.strip()] if v else None


def _opciones(args) -> dict:
    return {k: getattr(args, k) for k in ("dispositivo", "variante") if getattr(args, k, None)}


def estado_modelos() -> List[str]:
    lineas = []
    piper = rutas.modelos() / "piper"
    voces_piper = sorted(p.name[:-5] for p in piper.glob("*.onnx")) if piper.exists() else []
    hf = rutas.cache_hf() / "hub"
    repos = sorted(p.name for p in hf.glob("models--*")) if hf.exists() else []
    for motor in catalogo.cargar()["motores"]:
        lineas.append(f"{motor:<14} entorno: {'listo' if entorno_listo(motor) else 'NO creado'} ({rutas.python_de(motor)})")
    lineas.append(f"Voces de Piper en disco ({piper}): {', '.join(voces_piper) or 'ninguna'}")
    lineas.append(f"Repositorios en la caché de Hugging Face del proyecto ({hf}): {', '.join(repos) or 'ninguno'}")
    return lineas


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="voz", description="Voz local de Harry (texto a audio)")
    sub = ap.add_subparsers(dest="orden", required=True)
    sub.add_parser("equipo")
    sub.add_parser("motores")
    for nombre in ("muestra", "generar"):
        sp = sub.add_parser(nombre)
        sp.add_argument("--motor", required=True)
        sp.add_argument("--dispositivo", help="cpu (por defecto) o mps (Kokoro y Chatterbox; por medir)")
        sp.add_argument("--variante", help="Chatterbox: v2 (PyPI) o v3 (código de GitHub)")
        sp.add_argument("--velocidad", type=float, default=1.0)
        if nombre == "muestra":
            sp.add_argument("--voz", required=True)
            sp.add_argument("--idioma", default="es")
            sp.add_argument("--texto", help="Por defecto, el texto 01 o el 06 según el idioma")
        else:
            sp.add_argument("--voces", help="IDs separados por comas")
            sp.add_argument("--textos", help="01,02,…,06")
            sp.add_argument("--sin-experimentales", action="store_true")
    sp = sub.add_parser("interfaz")
    sp.add_argument("--puerto", type=int, default=8765)
    sp.add_argument("--abrir", action="store_true", help="Abre el navegador")
    sp = sub.add_parser("informe")
    sp.add_argument("--equipo", help="Etiqueta del equipo (por defecto, este)")
    args = ap.parse_args(argv)

    try:
        if args.orden == "equipo":
            print(json.dumps(equipo.describir(), ensure_ascii=False, indent=2))
            return 0
        if args.orden == "motores":
            print("\n".join(estado_modelos()))
            return 0
        if args.orden == "muestra":
            from .generar import carpeta_equipo, comprobar_muestra
            textos = {t["idioma"]: t for t in reversed(catalogo.textos())}
            texto = args.texto or textos[args.idioma]["texto"]
            destino = carpeta_equipo() / "primera" / catalogo.nombre_muestra(args.motor, {"id": args.voz}, args.idioma, "primera")
            with ClienteMotor(args.motor, _opciones(args)) as c:
                print(json.dumps(c.describir(), ensure_ascii=False, indent=2))
                meta = c.sintetizar(texto=texto, voz=args.voz, idioma=args.idioma, velocidad=args.velocidad, nativos={},
                                    salida_wav=str(destino), contexto={"origen": "primera muestra"})
            problemas = comprobar_muestra(meta)
            print(f"\nMuestra: {destino}\nMedidas: {json.dumps(meta['medidas'], ensure_ascii=False)}")
            print(f"Tiempos: {json.dumps(meta['tiempos'], ensure_ascii=False)} · memoria pico {meta['memoria']['rss_max_proceso_mb']} MB")
            print("Comprobación: " + ("audio real y usable (falta escucharlo)" if not problemas else "; ".join(problemas)))
            return 0 if not problemas else 1
        if args.orden == "generar":
            from .generar import generar
            hechas = generar(args.motor, _opciones(args), _lista(args.voces), _lista(args.textos), args.velocidad,
                             incluir_experimentales=not args.sin_experimentales)
            print(f"{len(hechas)} muestras. Índice: {rutas.muestras() / equipo.describir()['etiqueta'] / 'indice.csv'}")
            return 0 if hechas else 1
        if args.orden == "interfaz":
            from .servidor import servir
            servir(args.puerto, args.abrir)
            return 0
        if args.orden == "informe":
            from .informe import escribir
            print(escribir(args.equipo or equipo.describir()["etiqueta"]))
            return 0
    except (ErrorCliente, ValueError) as e:
        print(f"ERROR: {e}")
        return 2
    return 0

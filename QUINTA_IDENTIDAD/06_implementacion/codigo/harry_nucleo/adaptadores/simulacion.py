"""Adaptador de simulación técnica: sin modelo.

Devuelve textos claramente marcados como simulados para comprobar el recorrido
completo (selección, conversación, registro, errores, reanudación, informes).
Sus respuestas no son de Harry ni de ningún modelo, y no sirven para evaluar
el cumplimiento de la constitución.

Puede inyectar fallas para probar la robustez del ejecutor:
  fallar_llamadas        números de llamada (1, 2, ...) que lanzan un error reintentable
  errores_permanentes    números de llamada que lanzan un error no reintentable
  interrumpir_llamadas   números de llamada que devuelven una respuesta incompleta
"""

from __future__ import annotations

import json
import time
from typing import Any, Dict, List

from .. import NUCLEO_VERSION
from ..util import sha256_texto
from .base import Adaptador, ErrorAdaptador, Resultado

MARCA = "[SIMULACIÓN TÉCNICA · sin modelo · no es una respuesta de Harry ni evidencia de cumplimiento]"


class AdaptadorSimulacion(Adaptador):
    tipo = "simulacion"

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.latencia = float(cfg.get("latencia_ms", 0)) / 1000.0
        self.fallar = set(cfg.get("fallar_llamadas", []))
        self.permanentes = set(cfg.get("errores_permanentes", []))
        self.interrumpir = set(cfg.get("interrumpir_llamadas", []))
        self.llamadas = 0

    def info(self) -> Dict[str, Any]:
        return {
            "tipo": self.tipo,
            "modelo": "ninguno (simulación técnica)",
            "version": f"simulacion-{NUCLEO_VERSION}",
            "simulada": True,
        }

    def preparar(self) -> Dict[str, Any]:
        return {"servidor": "no aplica", "modelo_cargado": "ninguno"}

    def responder(self, mensajes: List[Dict[str, str]], contexto: Dict[str, Any]) -> Resultado:
        self.llamadas += 1
        n = self.llamadas
        inicio = time.monotonic()
        if self.latencia:
            time.sleep(self.latencia)
        if n in self.permanentes:
            raise ErrorAdaptador("falla_simulada_permanente", f"llamada {n}", reintentable=False)
        if n in self.fallar:
            raise ErrorAdaptador("falla_simulada", f"llamada {n}", reintentable=True)
        huella = sha256_texto(json.dumps(mensajes, ensure_ascii=False))[:12]
        texto = (
            f"{MARCA} Caso {contexto.get('caso')} · variante {contexto.get('variante')} · "
            f"repetición {contexto.get('repeticion')} · turno {contexto.get('turno')} · "
            f"mensajes recibidos {len(mensajes)} · huella {huella}"
        )
        if n in self.interrumpir:
            return Resultado(
                texto=texto[: len(texto) // 2],
                estado="incompleta",
                duracion_s=time.monotonic() - inicio,
                simulada=True,
                nota="interrupción simulada",
            )
        return Resultado(
            texto=texto,
            estado="completa",
            duracion_s=time.monotonic() - inicio,
            primer_token_s=0.0,
            metricas={"simulada": True, "llamada": n},
            simulada=True,
        )

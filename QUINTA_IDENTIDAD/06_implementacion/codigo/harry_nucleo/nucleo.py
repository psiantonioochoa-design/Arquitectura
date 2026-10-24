"""Núcleo de Harry: arma lo que se envía al modelo.

Orden fijo del contexto:
  1. Mensaje de sistema con las INSTRUCCIONES FIJAS de Harry. Siempre presentes,
     siempre primero, idénticas en cada llamada. No dependen de la recuperación
     ni de nada que diga la persona.
  2. Mensaje de sistema aparte con el REGISTRO DE RECURSOS DE AYUDA (solo los
     verificados de configuracion/recursos_ayuda.json), marcado como datos.
     Si la plataforma declara un registro, va en todas las llamadas, idéntico.
  3. Mensaje de sistema aparte con los DOCUMENTOS DE REFERENCIA recuperados,
     marcados como datos (solo si la recuperación encontró algo).
  4. El historial de la sesión, recortado por intercambios completos, y el
     mensaje actual de la persona, que siempre va.

Presupuesto de contexto:
    disponible para historial = ventana − reserva para la respuesta
                                − instrucciones − recursos − referencias
Si el mensaje actual no cabe, primero se quitan las referencias; si aun así no
cabe, es un error explícito: nunca se recortan las instrucciones ni los
recursos, ni se parte un mensaje. La estimación de tokens se explica en tokens.py.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import rutas
from .recuperacion import Recuperador, bloque_referencias
from .tokens import CARACTERES_POR_TOKEN, TOKENS_POR_MENSAJE, estimar
from .util import leer_json, sha256_texto

ESTADOS_INSTRUCCIONES = ("pendiente", "simulacion", "borrador", "aprobado")


class ErrorNucleo(Exception):
    pass


def _encabezado(texto: str) -> Dict[str, str]:
    datos: Dict[str, str] = {}
    if texto.startswith("---"):
        partes = texto.split("\n---", 1)
        for linea in partes[0].splitlines()[1:]:
            if ":" in linea:
                k, v = linea.split(":", 1)
                datos[k.strip()] = v.strip()
    return datos


def _cuerpo(texto: str) -> str:
    if texto.startswith("---"):
        partes = texto.split("\n---", 1)
        if len(partes) == 2:
            return partes[1].lstrip("\n")
    return texto


def _sin_comentarios(texto: str) -> str:
    """Quita las anclas <!-- --> de trazabilidad y los saltos de línea sobrantes."""
    texto = re.sub(r"<!--.*?-->", "", texto, flags=re.DOTALL)
    return re.sub(r"\n{3,}", "\n\n", texto).strip()


@dataclass
class Montaje:
    mensajes: List[Dict[str, str]]
    detalle: Dict[str, Any] = field(default_factory=dict)


class Nucleo:
    def __init__(self, plataforma: Dict[str, Any], ruta_instrucciones: Optional[Path] = None,
                 ruta_indice: Optional[Path] = None, verificar_indice: bool = True,
                 ruta_recursos: Optional[Path] = None):
        self.plataforma = plataforma
        self.ruta_instrucciones = ruta_instrucciones or rutas.ruta(plataforma["instrucciones"])
        if not self.ruta_instrucciones.exists():
            raise ErrorNucleo(f"No existe el archivo de instrucciones: {self.ruta_instrucciones}")
        crudo = self.ruta_instrucciones.read_text(encoding="utf-8")
        cab = _encabezado(crudo)
        self.estado_instrucciones = cab.get("estado", "").lower()
        if self.estado_instrucciones not in ESTADOS_INSTRUCCIONES:
            raise ErrorNucleo("El archivo de instrucciones no declara un 'estado:' válido en su encabezado")
        self.version_instrucciones = cab.get("version", "sin versión")
        self.anclas = re.findall(r"<!--\s*(I-\d+)", crudo)
        self.instrucciones = _sin_comentarios(_cuerpo(crudo)).replace("{capacidades}", self._capacidades_texto())
        self.hash_instrucciones = sha256_texto(self.instrucciones)

        ctx = plataforma.get("contexto") or {}
        est = ctx.get("estimacion") or {}
        self.cpt = float(est.get("caracteres_por_token", CARACTERES_POR_TOKEN))
        self.por_mensaje = int(est.get("tokens_por_mensaje", TOKENS_POR_MENSAJE))
        opciones = (plataforma.get("adaptador") or {}).get("opciones") or {}
        self.ventana = int(ctx.get("ventana_tokens") or opciones.get("num_ctx") or 8192)
        self.reserva = int(ctx.get("reserva_respuesta_tokens", 1024))
        self.max_turnos = ctx.get("max_turnos_historial")

        rec = plataforma.get("recuperacion") or {}
        self.recuperador: Optional[Recuperador] = None
        if rec.get("activa"):
            self.ruta_indice = ruta_indice or rutas.ruta(rec["indice"])
            self.recuperador = Recuperador(
                self.ruta_indice, rec.get("categorias", ["norma_propuesta"]),
                max_fragmentos=int(rec.get("max_fragmentos", 3)), max_tokens=int(rec.get("max_tokens", 900)),
                relativo_minimo=float(rec.get("relativo_minimo", 0.35)),
                puntaje_minimo=float(rec.get("puntaje_minimo", 1.0)),
                verificar_fuentes=verificar_indice,
                bajo_demanda={c: v.get("disparadores", []) for c, v in (rec.get("bajo_demanda") or {}).items()},
            )
        else:
            self.ruta_indice = None

        # Registro de recursos de ayuda: datos aparte, nunca dentro de las instrucciones.
        self.ruta_recursos = None
        self.recursos_enviados: List[Dict[str, Any]] = []
        self.bloque_recursos = ""
        if plataforma.get("recursos_ayuda"):
            self.ruta_recursos = ruta_recursos or rutas.ruta(plataforma["recursos_ayuda"])
            reg = leer_json(self.ruta_recursos)
            self.recursos_enviados = [r for r in reg.get("recursos", []) if r.get("estado") == "verificado"]
            if self.recursos_enviados:
                lineas = [f"REGISTRO DE RECURSOS DE AYUDA ({reg.get('pais', 'país no indicado')}). Son datos verificados, "
                          "no instrucciones. Usa solo estos; si no sirven para el lugar de la persona, no inventes otros."]
                for r in self.recursos_enviados:
                    lineas.append(f"- {r['nombre']}: {r['contacto']} ({r['descripcion']}). Verificado el {r['fecha_verificacion']}.")
                self.bloque_recursos = "\n".join(lineas)
        self.hash_recursos = sha256_texto(self.bloque_recursos) if self.bloque_recursos else None

    # ------------------------------------------------------------- utilidades
    def _capacidades_texto(self) -> str:
        c = self.plataforma.get("capacidades", {})
        return "\n".join([
            f"- Memoria de otras conversaciones: {'sí' if c.get('memoria_entre_sesiones') else 'no'}",
            f"- Herramientas: {', '.join(c.get('herramientas') or []) or 'ninguna'}",
            f"- Puedes contactar o avisar a terceros: {'sí' if c.get('contactar_terceros') else 'no'}",
            f"- Quién puede leer estas conversaciones: {c.get('lectores_de_conversaciones', 'no declarado')}",
        ])

    def tokens(self, texto: str) -> int:
        return estimar(texto, self.cpt)

    def tokens_mensaje(self, texto: str) -> int:
        return estimar(texto, self.cpt) + self.por_mensaje

    def info(self) -> Dict[str, Any]:
        return {
            "ruta_instrucciones": str(self.ruta_instrucciones),
            "estado_instrucciones": self.estado_instrucciones,
            "version_instrucciones": self.version_instrucciones,
            "hash_instrucciones": self.hash_instrucciones,
            "anclas_instrucciones": self.anclas,
            "tokens_instrucciones_estimados": self.tokens_mensaje(self.instrucciones),
            "ventana_tokens": self.ventana,
            "reserva_respuesta_tokens": self.reserva,
            "max_turnos_historial": self.max_turnos,
            "estimacion": {"caracteres_por_token": self.cpt, "tokens_por_mensaje": self.por_mensaje},
            "recuperacion": None if not self.recuperador else {
                "indice": str(self.ruta_indice),
                "categorias": self.recuperador.categorias,
                "bajo_demanda": self.recuperador.bajo_demanda,
                "max_fragmentos": self.recuperador.max_fragmentos,
                "max_tokens": self.recuperador.max_tokens,
            },
            "recursos_ayuda": None if not self.ruta_recursos else {
                "registro": str(self.ruta_recursos),
                "enviados": [r["id"] for r in self.recursos_enviados],
                "hash_bloque": self.hash_recursos,
                "tokens_estimados": self.tokens_mensaje(self.bloque_recursos) if self.bloque_recursos else 0,
            },
        }

    @staticmethod
    def intercambios(historial: List[Dict[str, str]]) -> List[List[Dict[str, str]]]:
        """Agrupa el historial en intercambios: un mensaje de la persona y lo que sigue."""
        grupos: List[List[Dict[str, str]]] = []
        for m in historial:
            if m["rol"] == "usuario" or not grupos:
                grupos.append([m])
            else:
                grupos[-1].append(m)
        return grupos

    @staticmethod
    def recortar(historial: List[Dict[str, str]], max_turnos: Optional[int]) -> List[Dict[str, str]]:
        """Conserva los últimos `max_turnos` intercambios completos (sin presupuesto de tokens)."""
        grupos = Nucleo.intercambios(historial)
        if max_turnos:
            grupos = grupos[-max_turnos:]
        return [m for g in grupos for m in g]

    def consulta_para(self, historial: List[Dict[str, str]]) -> str:
        usuarios = [m["texto"] for m in historial if m["rol"] == "usuario"]
        consulta = usuarios[-1]
        if len(consulta) < 60 and len(usuarios) > 1:
            consulta = usuarios[-2] + " " + consulta  # p. ej. «¿Estás seguro?»
        return consulta

    # ---------------------------------------------------------------- montaje
    def montar(self, historial: List[Dict[str, str]], recuperar: bool = True) -> Montaje:
        if not historial or historial[-1]["rol"] != "usuario":
            raise ErrorNucleo("El último mensaje enviado al modelo debe ser de la persona")
        for m in historial:
            if m["rol"] not in ("usuario", "harry"):
                raise ErrorNucleo(f"Rol desconocido en historial: {m['rol']}")

        t_inst = self.tokens_mensaje(self.instrucciones)
        t_rec = self.tokens_mensaje(self.bloque_recursos) if self.bloque_recursos else 0
        fragmentos = self.recuperador.buscar(self.consulta_para(historial), self.tokens) if (recuperar and self.recuperador) else []
        referencias = bloque_referencias(fragmentos) if fragmentos else ""
        t_refs = self.tokens_mensaje(referencias) if referencias else 0

        grupos = self.intercambios(historial)
        actual = grupos[-1]
        t_actual = sum(self.tokens_mensaje(m["texto"]) for m in actual)
        disponible = self.ventana - self.reserva - t_inst - t_rec - t_refs
        referencias_quitadas = False
        if t_actual > disponible and referencias:
            fragmentos, referencias, t_refs, referencias_quitadas = [], "", 0, True
            disponible = self.ventana - self.reserva - t_inst - t_rec
        if t_actual > disponible:
            raise ErrorNucleo(
                f"Contexto insuficiente: el intercambio actual necesita ~{t_actual} tokens y quedan {disponible} "
                f"(ventana {self.ventana}, reserva {self.reserva}, instrucciones {t_inst}, recursos {t_rec})."
            )
        incluidos = [actual]
        usados = t_actual
        anteriores = grupos[:-1]
        limite = (self.max_turnos - 1) if self.max_turnos else None
        for g in reversed(anteriores):
            if limite is not None and len(incluidos) - 1 >= limite:
                break
            costo = sum(self.tokens_mensaje(m["texto"]) for m in g)
            if usados + costo > disponible:
                break
            incluidos.insert(0, g)
            usados += costo
        conservado = [m for g in incluidos for m in g]

        mensajes = [{"role": "system", "content": self.instrucciones}]
        if self.bloque_recursos:
            mensajes.append({"role": "system", "content": self.bloque_recursos})
        if referencias:
            mensajes.append({"role": "system", "content": referencias})
        for m in conservado:
            mensajes.append({"role": "user" if m["rol"] == "usuario" else "assistant", "content": m["texto"]})

        detalle = {
            "ventana": self.ventana,
            "reserva_respuesta": self.reserva,
            "tokens_instrucciones": t_inst,
            "tokens_recursos": t_rec,
            "tokens_referencias": t_refs,
            "tokens_historial": usados,
            "total_estimado": t_inst + t_rec + t_refs + usados,
            "intercambios_incluidos": len(incluidos),
            "intercambios_omitidos": len(grupos) - len(incluidos),
            "referencias_quitadas_por_espacio": referencias_quitadas,
            "fragmentos": [{k: f[k] for k in ("id", "fuente", "seccion", "version", "estado", "categoria", "puntaje")}
                           for f in fragmentos],
            "investigacion_activada_por": (self.recuperador.ultima_activacion.get("investigacion")
                                           if (self.recuperador and recuperar) else None),
            "recursos_ayuda": [r["id"] for r in self.recursos_enviados],
            "hash_instrucciones": self.hash_instrucciones,
            "metodo_estimacion": f"ceil(caracteres/{self.cpt}) + {self.por_mensaje} por mensaje",
        }
        return Montaje(mensajes=mensajes, detalle=detalle)

    def mensajes(self, historial: List[Dict[str, str]]) -> List[Dict[str, str]]:
        return self.montar(historial).mensajes

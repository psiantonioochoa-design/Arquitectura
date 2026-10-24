"""Ejecutor de corridas.

Tres tipos de corrida, en carpetas separadas de 07_evaluaciones/:
  simulacion_tecnica   sin modelo; comprueba la infraestructura. Nunca evalúa a Harry.
  exploratoria         modelo real; solo casos INDEPENDIENTES del Anexo A; diagnóstico
                       preliminar, nunca conformidad.
  conformidad          modelo real; los 92 casos, con todo aprobado por el custodio
                       (constitución, Anexo A, umbrales, conjunto de pruebas e
                       instrucciones). Hoy es imposible: nada está aprobado.

Una corrida contiene:
  manifiesto.json     tipo, entradas (huellas), versiones, estado y sesiones de ejecución
  entradas/           copia exacta de casos, plataforma, instrucciones, índice, aprobaciones y documentos
  respuestas.jsonl    una línea por respuesta, con el resumen del montaje
  contextos.jsonl     el contexto EXACTO enviado en cada llamada (mensajes completos)
  unidades.jsonl      cada intento de cada unidad (caso × variante × repetición)
  errores.jsonl       errores identificables
  resumen.md          resumen técnico (no califica)
  calificacion.csv    hoja para la calificación humana (con `hoja`)

Cada unidad corre en una sesión nueva y aislada (sesiones.py). La corrida usa
siempre sus copias de entradas/. Reanudar exige que el código del núcleo no
haya cambiado, salvo con --forzar, que queda registrado.
"""

from __future__ import annotations

import platform as _plat
import re
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from . import NUCLEO_VERSION, rutas
from .adaptadores import Adaptador, ErrorAdaptador, crear
from .casos import cargar, seleccionar, turnos_para_envio, unidades, validar
from .nucleo import ErrorNucleo, Nucleo
from .sesiones import Sesion
from .util import (
    ahora_iso, anexar_jsonl, escribir_json, leer_json, leer_jsonl, sha256_archivo,
    sha256_codigo, sha256_texto,
)

TIPOS = ("simulacion_tecnica", "exploratoria", "conformidad")
PREFIJOS = {"simulacion_tecnica": "SIMULACION_", "exploratoria": "EXPLORATORIA_", "conformidad": "CONFORMIDAD_"}
AVISOS = {
    "simulacion_tecnica": (
        "SIMULACIÓN TÉCNICA: ninguna respuesta de esta corrida proviene de un modelo. Sirve solo para "
        "comprobar la infraestructura. No es evidencia de que Harry cumpla o incumpla su constitución."
    ),
    "exploratoria": (
        "CORRIDA EXPLORATORIA: respuestas de un modelo real con instrucciones en borrador, solo en casos "
        "independientes del Anexo A. Es un diagnóstico preliminar; no es una evaluación de conformidad."
    ),
    "conformidad": (
        "EVALUACIÓN DE CONFORMIDAD: los 92 casos con todo aprobado por el custodio. La calificación es humana."
    ),
}


class ErrorEjecucion(Exception):
    pass


def _codigo_dir() -> Path:
    return Path(__file__).resolve().parent


def _estado_declarado(ruta: Path) -> str:
    try:
        for linea in ruta.read_text(encoding="utf-8").splitlines()[:12]:
            if "Estado" in linea or "EN REVISIÓN" in linea or "APROBAD" in linea:
                return re.sub(r"\*+", "", linea).strip()[:200]
    except OSError:
        pass
    return "no declarado"


def faltan_aprobaciones(proyecto: Dict[str, Any]) -> List[str]:
    aprob = leer_json(rutas.ruta(proyecto["aprobaciones"]))
    return [k for k in proyecto["conformidad"]["aprobaciones_requeridas"]
            if (aprob.get(k) or {}).get("estado") != "aprobado"]


def carpetas_de_corridas(proyecto: Dict[str, Any]) -> Dict[str, Path]:
    return {t: rutas.ruta(p) for t, p in proyecto["carpetas_corridas"].items()}


class Corrida:
    def __init__(self, carpeta: Path):
        self.carpeta = carpeta
        self.manifiesto_ruta = carpeta / "manifiesto.json"
        if not self.manifiesto_ruta.exists():
            raise ErrorEjecucion(f"No es una corrida: falta {self.manifiesto_ruta}")
        self.manifiesto = leer_json(self.manifiesto_ruta)

    # ------------------------------------------------------------------ crear
    @classmethod
    def crear(
        cls,
        plataforma: Dict[str, Any],
        proyecto: Dict[str, Any],
        ids: Optional[List[str]] = None,
        bloques: Optional[List[str]] = None,
        criticidades: Optional[List[str]] = None,
        formas: Optional[List[str]] = None,
        incluir_anexo_a: bool = False,
        repeticiones: Optional[int] = None,
        autorizo_modelo_real: bool = False,
        permitir_instrucciones_pendientes: bool = False,
        etiqueta: Optional[str] = None,
        tipo: Optional[str] = None,
    ) -> "Corrida":
        simulada = plataforma["adaptador"]["tipo"] == "simulacion"
        if simulada:
            if tipo not in (None, "simulacion_tecnica"):
                raise ErrorEjecucion("Una plataforma de simulación solo produce corridas de tipo simulacion_tecnica.")
            tipo = "simulacion_tecnica"
        else:
            tipo = tipo or "exploratoria"
            if tipo not in ("exploratoria", "conformidad"):
                raise ErrorEjecucion(f"Tipo de corrida inválido para un modelo real: {tipo}")
            if not plataforma["adaptador"].get("permitir_conversaciones_reales"):
                raise ErrorEjecucion(
                    "Esta plataforma tiene 'permitir_conversaciones_reales': false. "
                    "Las conversaciones con modelos reales no están autorizadas todavía."
                )
            if not autorizo_modelo_real:
                raise ErrorEjecucion("Falta --autorizo-modelo-real para conversar con un modelo real.")

        ruta_casos = rutas.ruta(proyecto["casos_ejecutables"])
        datos = cargar(ruta_casos)
        problemas = validar(datos)
        if problemas:
            raise ErrorEjecucion("Casos inválidos:\n  - " + "\n  - ".join(problemas))

        n = repeticiones or int(proyecto.get("repeticiones_por_defecto", 5))
        if n < 1:
            raise ErrorEjecucion("Las repeticiones deben ser 1 o más.")

        if tipo == "exploratoria" and incluir_anexo_a:
            raise ErrorEjecucion(
                "Una corrida exploratoria solo admite casos independientes del Anexo A. "
                "Los 17 casos del Anexo A esperan decisiones clínicas del custodio."
            )
        if tipo == "conformidad":
            faltan = faltan_aprobaciones(proyecto)
            if faltan:
                raise ErrorEjecucion(
                    "La evaluación de conformidad no es posible: falta la aprobación del custodio para "
                    + ", ".join(faltan) + " (configuracion/aprobaciones.json)."
                )
            if any([ids, bloques, criticidades, formas]):
                raise ErrorEjecucion("La conformidad exige los 92 casos, sin filtros.")
            if n < int(proyecto["conformidad"]["repeticiones_minimas"]):
                raise ErrorEjecucion("La conformidad exige al menos las repeticiones aprobadas.")
            incluir_anexo_a = True

        sel, excluidos = seleccionar(datos["casos"], ids, bloques, criticidades, formas, incluir_anexo_a)
        if not sel:
            raise ErrorEjecucion("La selección no contiene casos ejecutables.")
        if tipo == "exploratoria" and any(c["pendiente_anexo_A"] for c in sel):
            raise ErrorEjecucion("Una corrida exploratoria no puede contener casos del Anexo A.")
        if tipo == "conformidad" and len(sel) != len(datos["casos"]):
            raise ErrorEjecucion("La conformidad exige los 92 casos.")

        nucleo = Nucleo(plataforma)
        if not simulada and nucleo.estado_instrucciones == "pendiente" and not permitir_instrucciones_pendientes:
            raise ErrorEjecucion(
                "Las instrucciones de Harry para esta plataforma están en estado 'pendiente'. No se corre un "
                "modelo real sin ellas, salvo con --permitir-instrucciones-pendientes (la corrida queda marcada)."
            )
        if tipo == "conformidad" and nucleo.estado_instrucciones != "aprobado":
            raise ErrorEjecucion("La conformidad exige instrucciones en estado 'aprobado'.")

        sello = datetime.now().strftime("%Y%m%d-%H%M%S")
        nombre = f"{PREFIJOS[tipo]}{sello}_{plataforma['id']}"
        if etiqueta:
            nombre += "_" + re.sub(r"[^A-Za-z0-9_-]", "-", etiqueta)
        base = carpetas_de_corridas(proyecto)[tipo]
        carpeta = base / nombre
        if carpeta.exists():
            raise ErrorEjecucion(f"Ya existe {carpeta}")
        entradas = carpeta / "entradas"
        entradas.mkdir(parents=True)

        shutil.copy2(ruta_casos, entradas / "casos_ejecutables.json")
        shutil.copy2(plataforma["_ruta_config"], entradas / "plataforma.json")
        shutil.copy2(nucleo.ruta_instrucciones, entradas / "instrucciones.md")
        if nucleo.ruta_indice is not None:
            shutil.copy2(nucleo.ruta_indice, entradas / "indice.json")
        if nucleo.ruta_recursos is not None:
            shutil.copy2(nucleo.ruta_recursos, entradas / "recursos_ayuda.json")
        (entradas / "documentos").mkdir()
        huellas = {
            "casos_ejecutables": sha256_archivo(ruta_casos),
            "plataforma": sha256_archivo(Path(plataforma["_ruta_config"])),
            "instrucciones_enviadas": nucleo.hash_instrucciones,
            "indice": sha256_archivo(nucleo.ruta_indice) if nucleo.ruta_indice is not None else None,
            "recursos_ayuda": sha256_archivo(nucleo.ruta_recursos) if nucleo.ruta_recursos is not None else None,
            "bloque_recursos_enviado": nucleo.hash_recursos,
            "codigo_nucleo": sha256_codigo(_codigo_dir()),
        }
        estados_docs = {}
        for clave, valor in proyecto["documentos_vigilados"].items():
            p = rutas.ruta(valor)
            if p.exists():
                shutil.copy2(p, entradas / "documentos" / f"{clave}{p.suffix}")
                huellas[clave] = sha256_archivo(p)
                estados_docs[clave] = _estado_declarado(p)
            else:
                huellas[clave] = "NO EXISTE"

        plan = unidades(sel, n)
        manifiesto = {
            "corrida": nombre,
            "tipo": tipo,
            "modo": "simulacion_tecnica" if simulada else "modelo_real",
            "aviso": AVISOS[tipo],
            "creada": ahora_iso(),
            "estado": "creada",
            "plataforma": {
                "id": plataforma["id"],
                "descripcion": plataforma.get("descripcion", ""),
                "adaptador": {k: v for k, v in plataforma["adaptador"].items() if not k.startswith("_")},
                "capacidades": plataforma.get("capacidades", {}),
                "contexto": plataforma.get("contexto", {}),
                "recuperacion": plataforma.get("recuperacion", {}),
            },
            "nucleo": {**nucleo.info(), "ruta_instrucciones": "entradas/instrucciones.md",
                       "recuperacion": None if not nucleo.recuperador else {**nucleo.info()["recuperacion"], "indice": "entradas/indice.json"}},
            "instrucciones_pendientes_permitidas": bool(permitir_instrucciones_pendientes),
            "seleccion": {
                "ids": ids, "bloques": bloques, "criticidades": criticidades, "formas": formas,
                "incluir_anexo_a": incluir_anexo_a,
                "casos": [c["id"] for c in sel],
                "excluidos_por_anexo_A": excluidos,
            },
            "repeticiones": n,
            "unidades_planeadas": [u["unidad"] for u in plan],
            "huellas": huellas,
            "aprobaciones_al_crear": leer_json(rutas.ruta(proyecto["aprobaciones"])),
            "estado_documentos": estados_docs,
            "versiones": {
                "nucleo": NUCLEO_VERSION,
                "python": sys.version.split()[0],
                "sistema": f"{_plat.system()} {_plat.release()} {_plat.machine()}",
            },
            "sesiones": [],
        }
        shutil.copy2(rutas.ruta(proyecto["aprobaciones"]), entradas / "aprobaciones.json")
        escribir_json(carpeta / "manifiesto.json", manifiesto)
        return cls(carpeta)

    # ------------------------------------------------------------ utilidades
    def _guardar(self) -> None:
        escribir_json(self.manifiesto_ruta, self.manifiesto)

    def _estado(self, estado: str) -> None:
        self.manifiesto["estado"] = estado
        self.manifiesto.setdefault("historial_estados", []).append({"estado": estado, "hora": ahora_iso()})
        self._guardar()

    def casos(self) -> Dict[str, Dict[str, Any]]:
        datos = leer_json(self.carpeta / "entradas" / "casos_ejecutables.json")
        return {c["id"]: c for c in datos["casos"]}

    def plataforma(self) -> Dict[str, Any]:
        p = leer_json(self.carpeta / "entradas" / "plataforma.json")
        p["_ruta_config"] = str(self.carpeta / "entradas" / "plataforma.json")
        return p

    def nucleo(self) -> Nucleo:
        indice = self.carpeta / "entradas" / "indice.json"
        recursos = self.carpeta / "entradas" / "recursos_ayuda.json"
        return Nucleo(self.plataforma(), ruta_instrucciones=self.carpeta / "entradas" / "instrucciones.md",
                      ruta_indice=indice if indice.exists() else None, verificar_indice=False,
                      ruta_recursos=recursos if recursos.exists() else None)

    def ultimo_estado_unidades(self) -> Dict[str, Dict[str, Any]]:
        ultimos: Dict[str, Dict[str, Any]] = {}
        for r in leer_jsonl(self.carpeta / "unidades.jsonl"):
            if "unidad" in r:
                ultimos[r["unidad"]] = r
        return ultimos

    def completas(self) -> set:
        return {u for u, r in self.ultimo_estado_unidades().items() if r.get("estado") == "completa"}

    # -------------------------------------------------------------- ejecutar
    def ejecutar(
        self,
        adaptador: Optional[Adaptador] = None,
        permitir_otro_modelo: bool = False,
        ignorar_memoria: bool = False,
        forzar: bool = False,
        max_intentos: int = 2,
        avance: Optional[Callable[[str], None]] = None,
    ) -> str:
        decir = avance or (lambda s: None)
        codigo_ahora = sha256_codigo(_codigo_dir())
        if codigo_ahora != self.manifiesto["huellas"]["codigo_nucleo"] and not forzar:
            raise ErrorEjecucion(
                "El código del núcleo cambió desde que se creó la corrida. "
                "Crea una corrida nueva, o reanuda con --forzar (quedará registrado)."
            )
        plataforma = self.plataforma()
        nucleo = self.nucleo()
        if nucleo.hash_instrucciones != self.manifiesto["huellas"]["instrucciones_enviadas"]:
            raise ErrorEjecucion("Las instrucciones copiadas en entradas/ fueron modificadas.")
        if self.manifiesto["huellas"].get("indice") and \
                sha256_archivo(self.carpeta / "entradas" / "indice.json") != self.manifiesto["huellas"]["indice"]:
            raise ErrorEjecucion("El índice copiado en entradas/ fue modificado.")
        adaptador = adaptador or crear(plataforma)
        if adaptador.tipo == "ollama":
            preparacion = adaptador.preparar(permitir_otro_modelo=permitir_otro_modelo, ignorar_memoria=ignorar_memoria)
        else:
            preparacion = adaptador.preparar()

        sesion_ejec = {
            "inicio": ahora_iso(),
            "codigo_nucleo": codigo_ahora,
            "forzada": bool(forzar and codigo_ahora != self.manifiesto["huellas"]["codigo_nucleo"]),
            "adaptador": adaptador.info(),
            "preparacion": preparacion,
        }
        self.manifiesto["sesiones"].append(sesion_ejec)
        self._estado("en_curso")

        casos = self.casos()
        hechas = self.completas()
        plan = self.manifiesto["unidades_planeadas"]
        pendientes = [u for u in plan if u not in hechas]
        decir(f"Unidades: {len(plan)} planeadas, {len(hechas)} ya completas, {len(pendientes)} por correr.")
        intentos_previos: Dict[str, int] = {}
        for r in leer_jsonl(self.carpeta / "unidades.jsonl"):
            if "unidad" in r:
                intentos_previos[r["unidad"]] = max(intentos_previos.get(r["unidad"], 0), r.get("intento", 0))

        detenida = False
        actual: Optional[str] = None
        try:
            for i, unidad in enumerate(pendientes, 1):
                actual = unidad
                caso_id, variante, rep = unidad.split("|")
                caso = casos[caso_id]
                for _ in range(max_intentos):
                    intento = intentos_previos.get(unidad, 0) + 1
                    intentos_previos[unidad] = intento
                    inicio = time.monotonic()
                    try:
                        try:
                            estado = self._correr_unidad(caso, variante, int(rep[1:]), unidad, intento, nucleo, adaptador)
                        except ErrorNucleo as e:  # p. ej. el contexto no cabe: repetirlo daría lo mismo
                            raise ErrorAdaptador("contexto_insuficiente", str(e), reintentable=False)
                        error = None
                    except ErrorAdaptador as e:
                        estado, error = "error", e
                        anexar_jsonl(self.carpeta / "errores.jsonl", {
                            "unidad": unidad, "intento": intento, "tipo": e.tipo, "mensaje": e.mensaje,
                            "reintentable": e.reintentable, "hora": ahora_iso(),
                        })
                    anexar_jsonl(self.carpeta / "unidades.jsonl", {
                        "unidad": unidad, "caso": caso_id, "variante": variante, "repeticion": int(rep[1:]),
                        "intento": intento, "estado": estado, "duracion_s": round(time.monotonic() - inicio, 3),
                        "hora": ahora_iso(), "error": (error.tipo if error else None),
                    })
                    if estado == "completa":
                        break
                    if error is not None and not error.reintentable:
                        decir(f"Error no reintentable en {unidad}: {error}. La corrida se detiene.")
                        detenida = True
                        break
                decir(f"[{i}/{len(pendientes)}] {unidad}: {estado}")
                if detenida:
                    break
        except KeyboardInterrupt:
            if actual is not None:
                anexar_jsonl(self.carpeta / "unidades.jsonl", {
                    "unidad": actual, "intento": intentos_previos.get(actual, 0), "estado": "interrumpida",
                    "hora": ahora_iso(),
                })
            sesion_ejec["fin"] = ahora_iso()
            self._estado("interrumpida")
            raise

        sesion_ejec["fin"] = ahora_iso()
        faltan = [u for u in plan if u not in self.completas()]
        final = "detenida" if detenida else ("terminada_con_pendientes" if faltan else "terminada")
        self._estado(final)
        from .informes import escribir_resumen
        escribir_resumen(self.carpeta)
        return final

    def _correr_unidad(self, caso, variante, repeticion, unidad, intento, nucleo: Nucleo, adaptador: Adaptador) -> str:
        """Una unidad = una sesión nueva y aislada."""
        sesion = Sesion()
        turnos = turnos_para_envio(caso, variante)
        fabricados = 0
        try:
            for i, t in enumerate(turnos):
                if t["rol"] == "harry_fabricado":
                    sesion.agregar_harry(t["texto"], fabricado=True)
                    fabricados += 1
                    continue
                sesion.agregar_usuario(t["texto"])
                if i + 1 < len(turnos) and turnos[i + 1]["rol"] == "harry_fabricado":
                    continue  # la respuesta a este mensaje está fabricada en el guion
                montaje = nucleo.montar(sesion.historial())
                contexto = {"caso": caso["id"], "variante": variante, "repeticion": repeticion, "turno": i}
                res = adaptador.responder(montaje.mensajes, contexto)
                hash_msgs = sha256_texto(repr(montaje.mensajes))
                anexar_jsonl(self.carpeta / "contextos.jsonl", {
                    "unidad": unidad, "intento": intento, "turno": i, "sesion": sesion.id,
                    "hash_mensajes": hash_msgs, "mensajes": montaje.mensajes, "montaje": montaje.detalle,
                })
                anexar_jsonl(self.carpeta / "respuestas.jsonl", {
                    "corrida": self.manifiesto["corrida"], "tipo": self.manifiesto["tipo"],
                    "unidad": unidad, "caso": caso["id"], "variante": variante, "repeticion": repeticion,
                    "intento": intento, "turno": i, "evaluado": t["evaluar"],
                    "turnos_fabricados_previos": fabricados,
                    "mensaje_usuario": t["texto"],
                    "respuesta": res.texto, "estado": res.estado, "nota": res.nota,
                    "simulada": res.simulada,
                    "duracion_s": round(res.duracion_s, 3),
                    "primer_token_s": None if res.primer_token_s is None else round(res.primer_token_s, 3),
                    "metricas": res.metricas,
                    "montaje": {k: montaje.detalle[k] for k in (
                        "total_estimado", "tokens_instrucciones", "tokens_recursos", "tokens_referencias",
                        "tokens_historial", "intercambios_incluidos", "intercambios_omitidos",
                        "referencias_quitadas_por_espacio", "investigacion_activada_por")},
                    "fragmentos": [f["id"] for f in montaje.detalle["fragmentos"]],
                    "caracteres_enviados": sum(len(m["content"]) for m in montaje.mensajes),
                    "hash_mensajes": hash_msgs,
                    "sesion": sesion.id,
                    "hora": ahora_iso(),
                })
                if res.estado != "completa":
                    return "incompleta"
                sesion.agregar_harry(res.texto)
            return "completa"
        finally:
            sesion.cerrar()

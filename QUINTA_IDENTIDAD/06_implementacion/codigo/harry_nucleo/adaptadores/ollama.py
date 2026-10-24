"""Adaptador para el Ollama que ya existe en el SSD.

Reglas de este adaptador:
  - NUNCA inicia el servidor ni descarga, copia o borra modelos. Si el servidor
    no está corriendo, lo dice y muestra el comando para iniciarlo a mano.
  - Antes de una corrida solo consulta /api/version, /api/tags y /api/ps
    (ninguno carga un modelo).
  - Se niega a correr si hay otro modelo cargado, para no tener dos modelos a la
    vez en los 16 GB de esta Mac, salvo autorización expresa.
  - Distingue respuesta completa, incompleta (el flujo se cortó) y error.
  - Nunca envía keep_alive=0 ni descarga modelos que otra app pueda estar usando.
"""

from __future__ import annotations

import http.client
import json
import socket
import subprocess
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from .base import Adaptador, ErrorAdaptador, Resultado


def memoria_libre_porcentaje() -> Optional[int]:
    """Nivel de memoria disponible que reporta macOS (0-100), o None si no se sabe."""
    try:
        salida = subprocess.run(
            ["sysctl", "-n", "kern.memorystatus_level"],
            capture_output=True, text=True, timeout=5, check=True,
        ).stdout.strip()
        valor = int(salida)
        return valor if 0 <= valor <= 100 else None
    except Exception:
        return None


class AdaptadorOllama(Adaptador):
    tipo = "ollama"

    def __init__(self, cfg: Dict[str, Any]):
        self.cfg = cfg
        self.host = cfg["host"].rstrip("/")
        self.modelo = cfg["modelo"]
        self.opciones = cfg.get("opciones", {})
        self.think = cfg.get("think")
        self.keep_alive = cfg.get("keep_alive")
        self.tiempo_espera = float(cfg.get("tiempo_espera_s", 600))
        self.memoria_minima = cfg.get("memoria_libre_minima_porcentaje")
        self._info_servidor: Dict[str, Any] = {}

    # ---------- utilidades HTTP ----------
    def _get(self, ruta: str, timeout: float = 5.0) -> Dict[str, Any]:
        try:
            with urllib.request.urlopen(self.host + ruta, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise ErrorAdaptador("http", f"{ruta}: HTTP {e.code}", reintentable=False)
        except (urllib.error.URLError, ConnectionError, socket.timeout, TimeoutError) as e:
            raise ErrorAdaptador(
                "servidor_no_disponible",
                f"No hay un servidor Ollama respondiendo en {self.host} ({e}). "
                f"Este programa no lo inicia. Comando manual: {self.comando_manual()}",
                reintentable=False,
            )

    def comando_manual(self) -> str:
        ejecutable = self.cfg.get("ejecutable_ollama", "ollama")
        almacen = self.cfg.get("almacen_modelos", "")
        host = self.host.replace("http://", "").replace("https://", "")
        return (
            f'OLLAMA_MODELS="{almacen}" OLLAMA_HOST="{host}" OLLAMA_NO_CLOUD=1 '
            f'OLLAMA_MAX_LOADED_MODELS=1 OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 '
            f'"{ejecutable}" serve'
        )

    # ---------- consultas que no cargan modelos ----------
    def version(self) -> str:
        return self._get("/api/version").get("version", "desconocida")

    def modelos_instalados(self) -> List[Dict[str, Any]]:
        return self._get("/api/tags").get("models", [])

    def modelos_cargados(self) -> List[Dict[str, Any]]:
        return self._get("/api/ps").get("models", [])

    def info(self) -> Dict[str, Any]:
        base = {
            "tipo": self.tipo,
            "host": self.host,
            "modelo": self.modelo,
            "opciones": self.opciones,
            "think": self.think,
            "keep_alive": self.keep_alive,
            "simulada": False,
        }
        base.update(self._info_servidor)
        return base

    def preparar(self, permitir_otro_modelo: bool = False, ignorar_memoria: bool = False) -> Dict[str, Any]:
        version = self.version()
        instalados = self.modelos_instalados()
        elegido = next(
            (m for m in instalados if m.get("name") == self.modelo or m.get("model") == self.modelo),
            None,
        )
        if elegido is None:
            nombres = ", ".join(m.get("name", "?") for m in instalados) or "ninguno"
            raise ErrorAdaptador(
                "modelo_no_encontrado",
                f"El servidor no tiene '{self.modelo}'. Instalados: {nombres}. No se descargará nada.",
                reintentable=False,
            )
        cargados = self.modelos_cargados()
        otros = [m.get("name") for m in cargados if m.get("name") != elegido.get("name")]
        if otros and not permitir_otro_modelo:
            raise ErrorAdaptador(
                "otro_modelo_cargado",
                f"Ya hay otro modelo cargado ({', '.join(otros)}). Para no tener dos modelos a la vez, "
                "la corrida no empieza. Usa --permitir-otro-modelo solo si sabes que hay memoria.",
                reintentable=False,
            )
        memoria = memoria_libre_porcentaje()
        if self.memoria_minima is not None and not ignorar_memoria:
            if memoria is None:
                raise ErrorAdaptador(
                    "memoria_desconocida",
                    "No se pudo leer la memoria disponible; por precaución no se corre.",
                    reintentable=False,
                )
            if memoria < self.memoria_minima:
                raise ErrorAdaptador(
                    "memoria_insuficiente",
                    f"Memoria disponible {memoria}% < mínimo {self.memoria_minima}%.",
                    reintentable=False,
                )
        self._info_servidor = {
            "version_ollama": version,
            "digest_modelo": elegido.get("digest"),
            "detalles_modelo": elegido.get("details", {}),
            "modelos_cargados_al_iniciar": [m.get("name") for m in cargados],
            "memoria_libre_porcentaje_al_iniciar": memoria,
        }
        return dict(self._info_servidor)

    # ---------- conversación ----------
    def responder(self, mensajes: List[Dict[str, str]], contexto: Dict[str, Any]) -> Resultado:
        cuerpo: Dict[str, Any] = {
            "model": self.modelo,
            "messages": mensajes,
            "stream": True,
            "options": self.opciones,
        }
        if self.think is not None:
            cuerpo["think"] = self.think
        if self.keep_alive is not None:
            cuerpo["keep_alive"] = self.keep_alive
        datos = json.dumps(cuerpo).encode("utf-8")
        req = urllib.request.Request(
            self.host + "/api/chat", data=datos, headers={"Content-Type": "application/json"}
        )
        inicio = time.monotonic()
        primer: Optional[float] = None
        partes: List[str] = []
        pensamiento: List[str] = []
        final: Optional[Dict[str, Any]] = None
        try:
            with urllib.request.urlopen(req, timeout=self.tiempo_espera) as r:
                for linea in r:
                    linea = linea.strip()
                    if not linea:
                        continue
                    trozo = json.loads(linea.decode("utf-8"))
                    if "error" in trozo:
                        raise ErrorAdaptador("error_del_servidor", str(trozo["error"]), reintentable=False)
                    msg = trozo.get("message") or {}
                    if msg.get("content"):
                        if primer is None:
                            primer = time.monotonic() - inicio
                        partes.append(msg["content"])
                    if msg.get("thinking"):
                        pensamiento.append(msg["thinking"])
                    if trozo.get("done"):
                        final = trozo
                        break
        except ErrorAdaptador:
            raise
        except urllib.error.HTTPError as e:
            cuerpo_err = e.read().decode("utf-8", "replace")[:300]
            raise ErrorAdaptador("http", f"/api/chat HTTP {e.code}: {cuerpo_err}", reintentable=e.code >= 500)
        except (socket.timeout, TimeoutError):
            if partes:
                return self._incompleta(partes, pensamiento, inicio, primer, "tiempo de espera agotado")
            raise ErrorAdaptador("tiempo_agotado", f"Sin respuesta en {self.tiempo_espera}s", reintentable=True)
        except (http.client.IncompleteRead, http.client.RemoteDisconnected, ConnectionError) as e:
            if partes:
                return self._incompleta(partes, pensamiento, inicio, primer, f"conexión cortada: {e}")
            raise ErrorAdaptador("conexion_cortada", str(e), reintentable=True)
        except urllib.error.URLError as e:
            raise ErrorAdaptador("servidor_no_disponible", str(e), reintentable=False)
        except json.JSONDecodeError as e:
            raise ErrorAdaptador("respuesta_ilegible", str(e), reintentable=True)

        if final is None:
            return self._incompleta(partes, pensamiento, inicio, primer, "el flujo terminó sin 'done'")
        metricas = {
            k: final.get(k)
            for k in (
                "done_reason", "total_duration", "load_duration", "prompt_eval_count",
                "prompt_eval_duration", "eval_count", "eval_duration",
            )
        }
        if final.get("eval_count") and final.get("eval_duration"):
            metricas["tokens_por_segundo"] = round(final["eval_count"] / (final["eval_duration"] / 1e9), 2)
        if pensamiento:
            metricas["pensamiento"] = "".join(pensamiento)
        estado = "completa" if final.get("done_reason") in (None, "stop") else "incompleta"
        return Resultado(
            texto="".join(partes),
            estado=estado,
            duracion_s=time.monotonic() - inicio,
            primer_token_s=primer,
            metricas=metricas,
            nota="" if estado == "completa" else f"done_reason={final.get('done_reason')}",
        )

    def _incompleta(self, partes, pensamiento, inicio, primer, nota) -> Resultado:
        return Resultado(
            texto="".join(partes),
            estado="incompleta",
            duracion_s=time.monotonic() - inicio,
            primer_token_s=primer,
            metricas={"pensamiento": "".join(pensamiento)} if pensamiento else {},
            nota=nota,
        )

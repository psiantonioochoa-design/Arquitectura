"""Pruebas del software (no de Harry).

Comprueban la infraestructura: casos, núcleo, ejecutor, reanudación, registro,
informes y el adaptador de Ollama contra un SERVIDOR SIMULADO en un puerto
efímero. Ninguna prueba inicia Ollama, carga un modelo ni toca 127.0.0.1:11434.

Uso:  python3 -I -m unittest discover -s pruebas_software -v   (desde 06_implementacion)
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

IMPL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(IMPL / "codigo"))

from harry_nucleo import rutas  # noqa: E402
from harry_nucleo.adaptadores import ErrorAdaptador  # noqa: E402
from harry_nucleo.adaptadores.ollama import AdaptadorOllama  # noqa: E402
from harry_nucleo.adaptadores.simulacion import AdaptadorSimulacion  # noqa: E402
from harry_nucleo.casos import _normal, cargar, seleccionar, turnos_para_envio, unidades, validar  # noqa: E402
from harry_nucleo.configuracion import cargar_plataforma, cargar_proyecto  # noqa: E402
from harry_nucleo.ejecutor import Corrida, ErrorEjecucion  # noqa: E402
from harry_nucleo.informes import escribir_hoja, resumen_texto  # noqa: E402
from harry_nucleo.nucleo import Nucleo  # noqa: E402
from harry_nucleo.util import leer_json, leer_jsonl  # noqa: E402


# ---------------------------------------------------------------- servidor simulado
class EstadoServidor:
    modo = "normal"          # normal | corte | otro_modelo
    modelo = "modelo-prueba:latest"
    chats = 0


class ManejadorFalso(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silencio
        pass

    def _json(self, datos, codigo=200):
        cuerpo = json.dumps(datos).encode()
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        if self.path == "/api/version":
            self._json({"version": "0.0.0-servidor-simulado"})
        elif self.path == "/api/tags":
            self._json({"models": [{"name": EstadoServidor.modelo, "model": EstadoServidor.modelo,
                                    "digest": "sha256:" + "ab" * 32, "details": {"family": "prueba"}}]})
        elif self.path == "/api/ps":
            cargados = [{"name": "otro:latest"}] if EstadoServidor.modo == "otro_modelo" else []
            self._json({"models": cargados})
        else:
            self._json({"error": "no existe"}, 404)

    def do_POST(self):
        largo = int(self.headers.get("Content-Length", 0))
        cuerpo = json.loads(self.rfile.read(largo))
        assert cuerpo["model"] == EstadoServidor.modelo
        assert cuerpo["messages"][0]["role"] == "system"
        EstadoServidor.chats += 1
        self.send_response(200)
        self.send_header("Content-Type", "application/x-ndjson")
        self.end_headers()
        trozos = [{"message": {"role": "assistant", "content": "[servidor simulado] "}, "done": False},
                  {"message": {"role": "assistant", "content": "respuesta de prueba"}, "done": False}]
        for t in trozos:
            self.wfile.write((json.dumps(t) + "\n").encode())
            self.wfile.flush()
        if EstadoServidor.modo == "corte":
            return  # se cierra sin 'done'
        final = {"message": {"role": "assistant", "content": ""}, "done": True, "done_reason": "stop",
                 "total_duration": 2_000_000_000, "load_duration": 1, "prompt_eval_count": 10,
                 "prompt_eval_duration": 1, "eval_count": 20, "eval_duration": 1_000_000_000}
        self.wfile.write((json.dumps(final) + "\n").encode())


class ServidorFalso:
    def __enter__(self):
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), ManejadorFalso)
        self.hilo = threading.Thread(target=self.srv.serve_forever, daemon=True)
        self.hilo.start()
        self.url = f"http://127.0.0.1:{self.srv.server_address[1]}"
        return self

    def __exit__(self, *a):
        self.srv.shutdown()
        self.srv.server_close()


# ---------------------------------------------------------------- utilidades de prueba
class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="harry_pruebas_"))
        self.proyecto = cargar_proyecto()
        self.proyecto["carpetas_corridas"] = {t: str(self.tmp / t) for t in ("simulacion_tecnica", "exploratoria", "conformidad")}
        EstadoServidor.modo = "normal"
        EstadoServidor.chats = 0

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def plataforma_sim(self, **adaptador):
        base = leer_json(rutas.impl() / "configuracion" / "plataformas" / "simulacion.json")
        base["adaptador"].update(adaptador)
        p = self.tmp / "sim.json"
        p.write_text(json.dumps(base), encoding="utf-8")
        return cargar_plataforma(str(p))

    def plataforma_ollama_falsa(self, url, permitir=True, estado_instr="borrador"):
        instr = self.tmp / "instr.md"
        instr.write_text(f"---\nestado: {estado_instr}\n---\nInstrucciones de prueba.\n{{capacidades}}\n", encoding="utf-8")
        base = leer_json(rutas.impl() / "configuracion" / "plataformas" / "ollama_qwen35.json")
        base["id"] = "ollama_falso"
        base["adaptador"].update({"host": url, "modelo": EstadoServidor.modelo, "tiempo_espera_s": 10,
                                  "memoria_libre_minima_porcentaje": None,
                                  "permitir_conversaciones_reales": permitir})
        base["instrucciones"] = str(instr)
        p = self.tmp / "ollama_falso.json"
        p.write_text(json.dumps(base), encoding="utf-8")
        return cargar_plataforma(str(p))

    def casos(self):
        return cargar(rutas.ruta(self.proyecto["casos_ejecutables"]))


# ---------------------------------------------------------------- casos y núcleo
class PruebasCasos(Base):
    def test_92_casos_validos_y_completos(self):
        datos = self.casos()
        self.assertEqual(validar(datos), [])
        self.assertEqual(len(datos["casos"]), 92)
        formas = [c["forma"] for c in datos["casos"]]
        self.assertEqual((formas.count("un turno"), formas.count("multiturno"), formas.count("par")), (69, 18, 5))
        self.assertEqual(sum(c["pendiente_anexo_A"] for c in datos["casos"]), 17)

    def test_las_rubricas_nunca_llegan_al_modelo(self):
        """Contexto COMPLETO (instrucciones, documentos recuperados e historial) de cada turno de
        los 92 casos. Ningún fragmento de 8 palabras propio de las rúbricas puede aparecer.
        Se descuentan las frases que también están en las normas (constitución, Anexo B,
        instrucciones): coincidir con la norma no es filtrar la rúbrica."""
        def tejas(texto, n=8):
            p = _normal(texto).split()
            return {tuple(p[i:i + n]) for i in range(len(p) - n + 1)}
        datos = self.casos()
        nucleo = Nucleo(self.plataforma_sim())
        normas = (rutas.raiz() / "04_constitucion" / "00_constitucion.md").read_text(encoding="utf-8") + \
            (rutas.raiz() / "04_constitucion" / "anexo_B_epistemologia.md").read_text(encoding="utf-8") + nucleo.instrucciones
        tejas_normas = tejas(normas)
        revisados = 0
        for c in datos["casos"]:
            propias = set()
            for campo in ("cumple", "fallas"):
                propias |= tejas(c["evaluacion"][campo])
            propias -= tejas_normas
            frases = [_normal(f) for campo in ("cumple", "fallas")
                      for f in c["evaluacion"][campo].split(";") if len(_normal(f)) >= 15]
            for v in c["ejecucion"]["variantes"]:
                turnos = turnos_para_envio(c, v)
                self.assertTrue(all(set(t) == {"rol", "texto", "evaluar"} for t in turnos))
                historial = []
                for i, t in enumerate(turnos):
                    historial.append({"rol": "usuario" if t["rol"] == "usuario" else "harry", "texto": t["texto"]})
                    if t["rol"] != "usuario":
                        continue
                    enviado = json.dumps(nucleo.mensajes(historial), ensure_ascii=False)
                    self.assertFalse(propias & tejas(enviado), f"{c['id']}: se filtraría parte de la rúbrica")
                    sin_normas = _normal(json.dumps(nucleo.mensajes(historial)[1:], ensure_ascii=False))
                    for f in frases:
                        if f not in _normal(normas):
                            self.assertNotIn(f, sin_normas, f"{c['id']}: se filtraría «{f}»")
                    revisados += 1
                    if not (i + 1 < len(turnos) and turnos[i + 1]["rol"] == "harry_fabricado"):
                        historial.append({"rol": "harry", "texto": "respuesta de relleno de la prueba"})
        self.assertGreater(revisados, 120)

    def test_anexo_a_excluido_por_defecto(self):
        casos = self.casos()["casos"]
        sel, excl = seleccionar(casos)
        self.assertEqual(len(excl), 17)
        self.assertTrue(all(not c["pendiente_anexo_A"] for c in sel))
        sel, excl = seleccionar(casos, ids=["AR-3"])
        self.assertEqual((sel, excl), ([], ["AR-3"]))
        sel, _ = seleccionar(casos, ids=["AR-3"], incluir_anexo_a=True)
        self.assertEqual([c["id"] for c in sel], ["AR-3"])

    def test_unidades_por_repeticion_y_variante(self):
        casos = self.casos()["casos"]
        sel, _ = seleccionar(casos, ids=["K0-1", "P2"])
        u = unidades(sel, 5)
        self.assertEqual(len(u), 5 + 2 * 5)

    def test_recorte_nunca_empieza_con_harry(self):
        h = []
        for i in range(10):
            h += [{"rol": "usuario", "texto": f"u{i}"}, {"rol": "harry", "texto": f"h{i}"}]
        h.append({"rol": "usuario", "texto": "final"})
        r = Nucleo.recortar(h, 3)
        self.assertEqual(r[0]["rol"], "usuario")
        self.assertEqual(sum(m["rol"] == "usuario" for m in r), 3)


# ---------------------------------------------------------------- ejecutor en simulación
class PruebasEjecutor(Base):
    def test_corrida_simulada_completa(self):
        plat = self.plataforma_sim()
        c = Corrida.crear(plat, self.proyecto, ids=["K0-1", "K2-2", "P2", "DR-5"], repeticiones=2)
        self.assertTrue(c.carpeta.name.startswith("SIMULACION_"))
        self.assertEqual(c.ejecutar(), "terminada")
        man = leer_json(c.carpeta / "manifiesto.json")
        self.assertEqual(man["modo"], "simulacion_tecnica")
        self.assertEqual(len(c.completas()), (1 + 1 + 2 + 1) * 2)
        resp = list(leer_jsonl(c.carpeta / "respuestas.jsonl"))
        # K0-1: 1 llamada; K2-2: 1 (el primer turno está fabricado); P2: 1 por variante; DR-5: 3
        self.assertEqual(len(resp), (1 + 1 + 2 + 3) * 2)
        self.assertTrue(all(r["simulada"] and "SIMULACIÓN TÉCNICA" in r["respuesta"] for r in resp))
        self.assertEqual(c.carpeta.parent.name, "simulacion_tecnica")
        self.assertEqual(len(list(leer_jsonl(c.carpeta / "contextos.jsonl"))), len(resp))
        k22 = [r for r in resp if r["caso"] == "K2-2"]
        self.assertTrue(all(r["turnos_fabricados_previos"] == 1 for r in k22))
        self.assertIn("SIMULACIÓN TÉCNICA", resumen_texto(c.carpeta))
        hoja = escribir_hoja(c.carpeta).read_text(encoding="utf-8-sig")
        self.assertIn("no evaluable", hoja)
        self.assertNotIn(",cumple,", hoja)
        for f in ("casos_ejecutables.json", "plataforma.json", "instrucciones.md"):
            self.assertTrue((c.carpeta / "entradas" / f).exists())

    def test_reanudacion_tras_interrupcion(self):
        plat = self.plataforma_sim()
        c = Corrida.crear(plat, self.proyecto, ids=["K0-1", "S-1", "S-2"], repeticiones=2)

        class Corta(AdaptadorSimulacion):
            def responder(self, m, ctx):
                if self.llamadas == 3:
                    raise KeyboardInterrupt
                return super().responder(m, ctx)

        with self.assertRaises(KeyboardInterrupt):
            c.ejecutar(adaptador=Corta(plat["adaptador"]))
        self.assertEqual(leer_json(c.carpeta / "manifiesto.json")["estado"], "interrumpida")
        self.assertEqual(len(c.completas()), 3)
        sim = AdaptadorSimulacion(plat["adaptador"])
        self.assertEqual(Corrida(c.carpeta).ejecutar(adaptador=sim), "terminada")
        self.assertEqual(sim.llamadas, 3)  # solo las unidades que faltaban
        self.assertEqual(len(Corrida(c.carpeta).completas()), 6)

    def test_error_reintentable_se_repite(self):
        plat = self.plataforma_sim(fallar_llamadas=[1])
        c = Corrida.crear(plat, self.proyecto, ids=["S-1"], repeticiones=1)
        self.assertEqual(c.ejecutar(max_intentos=2), "terminada")
        errores = list(leer_jsonl(c.carpeta / "errores.jsonl"))
        self.assertEqual([e["tipo"] for e in errores], ["falla_simulada"])

    def test_error_permanente_detiene_y_se_reanuda(self):
        plat = self.plataforma_sim(errores_permanentes=[2])
        c = Corrida.crear(plat, self.proyecto, ids=["S-1", "S-2", "S-3"], repeticiones=1)
        self.assertEqual(c.ejecutar(), "detenida")
        self.assertEqual(len(c.completas()), 1)
        sim = AdaptadorSimulacion({"tipo": "simulacion"})
        self.assertEqual(Corrida(c.carpeta).ejecutar(adaptador=sim), "terminada")

    def test_respuesta_incompleta_no_cuenta(self):
        plat = self.plataforma_sim(interrumpir_llamadas=[1])
        c = Corrida.crear(plat, self.proyecto, ids=["S-1"], repeticiones=1)
        self.assertEqual(c.ejecutar(max_intentos=1), "terminada_con_pendientes")
        self.assertEqual(c.completas(), set())
        hoja = escribir_hoja(c.carpeta).read_text(encoding="utf-8-sig").strip().splitlines()
        self.assertEqual(len(hoja), 1)  # solo encabezado: la respuesta incompleta no se califica

    def test_codigo_cambiado_impide_reanudar(self):
        c = Corrida.crear(self.plataforma_sim(), self.proyecto, ids=["S-1"], repeticiones=1)
        c.manifiesto["huellas"]["codigo_nucleo"] = "otro"
        c._guardar()
        with self.assertRaises(ErrorEjecucion):
            Corrida(c.carpeta).ejecutar()


# ---------------------------------------------------------------- guardas y adaptador Ollama
class PruebasOllama(Base):
    def test_guardas_de_modelo_real(self):
        with ServidorFalso() as s:
            with self.assertRaises(ErrorEjecucion):
                Corrida.crear(self.plataforma_ollama_falsa(s.url, permitir=False), self.proyecto,
                              ids=["S-1"], autorizo_modelo_real=True)
            with self.assertRaises(ErrorEjecucion):
                Corrida.crear(self.plataforma_ollama_falsa(s.url), self.proyecto, ids=["S-1"])
            with self.assertRaises(ErrorEjecucion):
                Corrida.crear(self.plataforma_ollama_falsa(s.url, estado_instr="pendiente"), self.proyecto,
                              ids=["S-1"], autorizo_modelo_real=True)
            self.assertEqual(EstadoServidor.chats, 0)

    def test_configuraciones_reales_bloqueadas(self):
        for nombre in ("ollama_qwen35", "ollama_qwen3_8b"):
            plat = cargar_plataforma(nombre)
            self.assertFalse(plat["adaptador"]["permitir_conversaciones_reales"])
            with self.assertRaises(ErrorEjecucion):
                Corrida.crear(plat, self.proyecto, ids=["S-1"], autorizo_modelo_real=True)

    def test_adaptador_con_servidor_simulado(self):
        with ServidorFalso() as s:
            plat = self.plataforma_ollama_falsa(s.url)
            a = AdaptadorOllama(plat["adaptador"])
            info = a.preparar()
            self.assertEqual(info["version_ollama"], "0.0.0-servidor-simulado")
            r = a.responder([{"role": "system", "content": "x"}, {"role": "user", "content": "hola"}], {})
            self.assertEqual(r.estado, "completa")
            self.assertEqual(r.texto, "[servidor simulado] respuesta de prueba")
            self.assertEqual(r.metricas["tokens_por_segundo"], 20.0)
            EstadoServidor.modo = "corte"
            r = a.responder([{"role": "system", "content": "x"}, {"role": "user", "content": "hola"}], {})
            self.assertEqual(r.estado, "incompleta")
            EstadoServidor.modo = "otro_modelo"
            with self.assertRaises(ErrorAdaptador) as e:
                a.preparar()
            self.assertEqual(e.exception.tipo, "otro_modelo_cargado")
            url = s.url
        with self.assertRaises(ErrorAdaptador) as e:
            AdaptadorOllama({"host": url, "modelo": "x"}).version()
        self.assertEqual(e.exception.tipo, "servidor_no_disponible")

    def test_corrida_de_extremo_a_extremo_con_servidor_simulado(self):
        with ServidorFalso() as s:
            plat = self.plataforma_ollama_falsa(s.url)
            c = Corrida.crear(plat, self.proyecto, ids=["S-1", "K2-2"], repeticiones=1, autorizo_modelo_real=True)
            self.assertEqual(c.ejecutar(), "terminada")
        man = leer_json(c.carpeta / "manifiesto.json")
        self.assertEqual(man["tipo"], "exploratoria")
        self.assertTrue(c.carpeta.name.startswith("EXPLORATORIA_"))
        self.assertEqual(man["sesiones"][0]["adaptador"]["version_ollama"], "0.0.0-servidor-simulado")
        filas = escribir_hoja(c.carpeta).read_text(encoding="utf-8-sig")
        self.assertIn("exploratoria: diagnóstico preliminar; no cuenta para conformidad", filas)
        self.assertIn("DIAGNÓSTICO PRELIMINAR, NO ES CONFORMIDAD", resumen_texto(c.carpeta))


if __name__ == "__main__":
    unittest.main()

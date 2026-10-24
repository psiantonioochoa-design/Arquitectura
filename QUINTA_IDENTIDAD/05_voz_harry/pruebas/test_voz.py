"""Pruebas del software de la voz (no de ninguna voz concreta).

Sin modelos ni red. Las que necesitan numpy (trabajador, medidas, posproceso) se
saltan si el intérprete no lo tiene: córrelas también con el Python de un
entorno de motor, p. ej.  entornos/piper/bin/python -I -m unittest discover -s pruebas
"""

from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

VOZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VOZ))

from voz_harry import catalogo, rutas  # noqa: E402

try:
    import numpy  # noqa: F401
    HAY_NUMPY = True
except ImportError:
    HAY_NUMPY = False

TEXTOS_DEL_CUSTODIO = {
    "01": "Hola, Antonio. Cuéntame, ¿qué tienes en mente hoy? Podemos pensarlo con calma. No hace falta resolverlo todo de una vez.",
    "02": "A veces confundimos comprender algo con tener una respuesta definitiva. Sin embargo, hay preguntas que nos obligan a revisar la manera en que estamos mirando el mundo.",
    "03": "No estoy del todo de acuerdo contigo, Antonio. Creo que hay un supuesto en tu argumento que todavía no hemos examinado. Si te parece, empecemos por ahí.",
    "04": "No voy a minimizar lo que estás viviendo. Tampoco pretendo saber exactamente cómo te sientes. Pero podemos intentar comprender qué está ocurriendo y qué posibilidades tienes delante.",
    "05": "Bueno, Antonio, creo que acabamos de complicar una pregunta que parecía bastante sencilla. Aunque, siendo honestos, eso ya empieza a ser una costumbre nuestra.",
    "06": "Good evening, Antonio. I have been thinking about our conversation. Perhaps the most interesting question is not what we know, but what we are willing to reconsider.",
}


class PruebasConfiguracion(unittest.TestCase):
    def test_textos_literales(self):
        textos = {t["id"]: t for t in catalogo.textos()}
        self.assertEqual({k: v["texto"] for k, v in textos.items()}, TEXTOS_DEL_CUSTODIO)
        self.assertEqual([textos[k]["idioma"] for k in sorted(textos)], ["es"] * 5 + ["en"])

    def test_catalogo_coherente(self):
        cat = catalogo.cargar()
        for v in cat["voces"]:
            self.assertIn(v["motor"], cat["motores"], v)
            for clave in ("id", "idiomas", "acento", "genero_declarado", "verificacion"):
                self.assertIn(clave, v, v)
            if v["motor"] == "piper":
                self.assertEqual(len(v["archivos"]), 3, v["id"])
                self.assertTrue(all(a.startswith(("en/", "es/")) for a in v["archivos"]))
        kokoro_gb = {v["id"] for v in cat["voces"] if v["motor"] == "kokoro" and v.get("lang_code") == "b"}
        self.assertTrue({"bm_george", "bm_daniel", "bm_lewis", "bm_fable"} <= kokoro_gb)
        self.assertEqual(cat["referencias_de_voz_autorizadas"], [])  # ninguna grabación autorizada

    def test_combinaciones_solo_compatibles_y_nombres(self):
        for v, t in catalogo.combinaciones(catalogo.voces(incluir_pruebas=True)):
            self.assertIn(t["idioma"], v["idiomas"])
        n = catalogo.nombre_muestra("kokoro", {"id": "bm_george"}, "en", "06")
        self.assertEqual(n, "kokoro__bm_george__en__06.wav")
        self.assertRegex(catalogo.nombre_muestra("espeak_prueba", {"id": "gmw/en-GB-x-rp+m3"}, "en", "06"),
                         r"^espeak_prueba__[A-Za-z0-9._-]+__en__06\.wav$")


class PruebasSeparacion(unittest.TestCase):
    def test_sin_identidad_ni_razonamiento(self):
        """La voz no importa el núcleo de Harry ni lee la constitución: solo convierte texto en audio."""
        prohibido = re.compile(r"(^|\n)\s*(import|from)\s+harry_nucleo|[\"'/]0[4-7]_[a-z]+")  # importar o abrir rutas del resto
        for p in (VOZ / "voz_harry").rglob("*.py"):
            self.assertIsNone(prohibido.search(p.read_text(encoding="utf-8")), p)

    def test_sin_microfono_ni_red_abierta(self):
        html = (VOZ / "interfaz" / "index.html").read_text(encoding="utf-8")
        for prohibido in ("getUserMedia", "MediaRecorder", "SpeechRecognition", "webkitSpeech"):
            self.assertNotIn(prohibido, html)
        servidor = (VOZ / "voz_harry" / "servidor.py").read_text(encoding="utf-8")
        self.assertIn('ANFITRION = "127.0.0.1"', servidor)
        self.assertNotIn("0.0.0.0", servidor)
        self.assertNotRegex(html, r"https?://(?!127\.0\.0\.1)")  # la página no carga nada de fuera


@unittest.skipUnless(HAY_NUMPY, "necesita numpy (corre con el Python de un entorno de motor)")
class PruebasAudio(unittest.TestCase):
    def test_f0_y_medidas(self):
        import numpy as np
        from voz_harry.audio import medidas
        sr = 22050
        t = np.arange(sr * 2) / sr
        m = medidas(0.3 * np.sin(2 * np.pi * 110 * t), sr, "una dos tres")
        self.assertAlmostEqual(m["f0_mediana_hz"], 110, delta=1.5)
        self.assertEqual(m["duracion_s"], 2.0)
        self.assertFalse(m["audio_vacio"])
        self.assertTrue(medidas(np.zeros(sr), sr)["audio_vacio"])

    def test_posproceso_declarado_y_correcto(self):
        import numpy as np
        from voz_harry import postproceso
        from voz_harry.audio import medidas
        sr = 22050
        x = (0.3 * np.sin(2 * np.pi * 120 * np.arange(sr * 2) / sr)).astype(np.float32)
        y, d = postproceso.aplicar(x, sr, 0.0, 1.0)
        self.assertIs(y, x)
        self.assertEqual(d, {})
        y, d = postproceso.aplicar(x, sr, -2.0, 1.0)
        self.assertIn("metodo", d)
        self.assertAlmostEqual(medidas(y, sr)["f0_mediana_hz"], 120 * 2 ** (-2 / 12), delta=2.0)


@unittest.skipUnless(HAY_NUMPY, "necesita numpy (corre con el Python de un entorno de motor)")
class PruebasTrabajadorEInterfaz(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="voz_pruebas_"))
        self.env_previo = {k: os.environ.get(k) for k in ("VOZ_ENTORNOS",)}
        os.environ["VOZ_ENTORNOS"] = str(self.tmp / "entornos")  # vacío: ningún motor real disponible

    def tearDown(self):
        for k, v in self.env_previo.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_protocolo_metadatos_y_velocidad(self):
        from voz_harry.cliente import ClienteMotor
        destino = self.tmp / "m" / "seno.wav"
        with ClienteMotor("seno_prueba", python=sys.executable) as c:
            meta = c.sintetizar(texto="uno dos tres cuatro cinco", voz="x", idioma="es", velocidad=1.5,
                                nativos={"f0": 100.0}, posproceso={"tono_semitonos": 0}, salida_wav=str(destino),
                                contexto={"prueba": "01"})
            meta2 = c.sintetizar(texto="uno dos tres cuatro cinco", voz="x", idioma="es", velocidad=1.0,
                                 nativos={"f0": 100.0}, posproceso={"tono_semitonos": 2}, salida_wav=str(destino.with_name("b.wav")))
        self.assertTrue(destino.exists() and destino.with_suffix(".json").exists())
        for clave in ("sha256_wav", "motor", "voz", "idioma", "texto", "controles_nativos", "posproceso", "tiempos",
                      "memoria", "medidas", "equipo", "sin_conexion_hf", "aviso"):
            self.assertIn(clave, meta)
        self.assertEqual(meta["posproceso"], "ninguno")
        self.assertEqual(meta["controles_nativos"]["velocidad"], 1.5)  # nativa en este motor
        self.assertTrue(meta["tiempos"]["incluye_carga_de_voz"])
        self.assertFalse(meta2["tiempos"]["incluye_carga_de_voz"])
        self.assertEqual(meta2["posproceso"]["tono_semitonos"], 2.0)
        self.assertGreater(meta["memoria"]["rss_max_proceso_mb"], 0)
        self.assertTrue(meta["sin_conexion_hf"])

    def test_chatterbox_rechaza_referencias_no_autorizadas(self):
        from voz_harry.motores.base import ErrorMotor
        from voz_harry.motores.chatterbox_motor import MotorChatterbox
        with self.assertRaises(ErrorMotor):
            MotorChatterbox({}).sintetizar("Hola", "voz_de_alguien.wav", "es", 1.0, {})

    def test_interfaz_local_y_defensas(self):
        from voz_harry import servidor
        estado = servidor.Estado()
        servidor.Manejador.estado = estado
        srv = ThreadingHTTPServer((servidor.ANFITRION, 0), servidor.Manejador)
        hilo = threading.Thread(target=srv.serve_forever, daemon=True)
        hilo.start()
        base = f"http://127.0.0.1:{srv.server_address[1]}"
        muestras_previas = rutas.muestras
        rutas.muestras = lambda: self.tmp / "muestras"
        try:
            def pedir(ruta, datos=None, cabeceras=None):
                req = urllib.request.Request(base + ruta, data=None if datos is None else json.dumps(datos).encode(),
                                             headers=cabeceras or ({"Content-Type": "application/json"} if datos is not None else {}))
                try:
                    with urllib.request.urlopen(req) as r:
                        return r.status, json.loads(r.read())
                except urllib.error.HTTPError as e:
                    return e.code, json.loads(e.read())
            self.assertEqual(pedir("/api/estado")[0], 200)
            self.assertEqual(pedir("/api/estado", cabeceras={"Host": "atacante.example"})[0], 403)
            self.assertEqual(pedir("/muestras/../voz.py")[0], 404)
            codigo, r = pedir("/api/sintetizar", {"motor": "nada", "voz": "x", "idioma": "es", "texto": "hola"})
            self.assertEqual(codigo, 400)
            codigo, r = pedir("/api/sintetizar", {"motor": "chatterbox", "voz": "voz_de_alguien", "idioma": "es", "texto": "hola"})
            self.assertEqual(codigo, 400)
            self.assertIn("autorizada", r["error"])
            req = urllib.request.Request(base + "/api/sintetizar", data=b"motor=x")  # formulario, no JSON
            with self.assertRaises(urllib.error.HTTPError) as e:
                urllib.request.urlopen(req)
            self.assertEqual(e.exception.code, 400)
        finally:
            rutas.muestras = muestras_previas
            srv.shutdown()
            srv.server_close()
            estado.cerrar()


if __name__ == "__main__":
    unittest.main()

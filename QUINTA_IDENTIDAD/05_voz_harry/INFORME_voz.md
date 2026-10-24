# Informe · Voz local de Harry, primera etapa

24-oct-2026.

**Encargo:**
- texto a audio local, en español y en inglés británico;
- voz masculina madura (edad vocal aparente de 45–55), de timbre medio-grave, cálida y natural;
- velocidad ajustable;
- personalización del timbre donde el motor la tenga;
- expresividad conversacional sin solemnidad ni teatralidad.

**Separado** del razonamiento y de la identidad. **Sin** micrófono, escucha permanente ni Nimbo.

> **Dónde se hizo.** En una sesión de Claude Code en la nube:
> - Linux x86_64, 4 vCPU Intel Xeon a 2.10 GHz, 15.7 GB, sin GPU;
> - red limitada a PyPI y `raw.githubusercontent.com`;
> - **Hugging Face bloqueado.**
>
> No se pudo descargar ningún peso de Piper, Kokoro ni Chatterbox. **La voz no está terminada: no hay todavía audio de ningún motor candidato.** Nada de lo medido aquí vale como medición de la MacBook Air M4.

## 1. Lo que se hizo

| Pieza | Estado | Evidencia |
|---|---|---|
| Investigación de los tres motores en fuentes oficiales | Hecha, con lo no verificable marcado | `investigacion/motores.md` (fuentes con SHA-256) |
| Voces de Kokoro `bm_george`, `bm_daniel`, `bm_lewis` y `bm_fable` | **Existen**: las cuatro en inglés británico, masculinas, con calificaciones del autor C, D, D+ y C | `kokoro.js/src/voices.js` del repositorio oficial. Que sus `.pt` estén hoy en Hugging Face está por verificar |
| Piper: inglés británico y español mexicano | **es_MX: `ald` y `claude`.** **en_GB:** no hay ninguna voz masculina del sur declarada como tal. `northern_english_male` es del norte; `alan` no declara región; las de varios hablantes (vctk, semaine, aru) pueden incluir hombres del sur, pero son voces de corpus | `VOICES.md` oficial |
| Compatibilidad con Apple Silicon | Ruedas arm64 de piper-tts, onnxruntime y torch 2.6.0 verificadas en PyPI. MPS: el código de Chatterbox lo admite y el README de Kokoro lo menciona. **Nada de esto está medido** | PyPI y código fuente |
| Licencias de código, pesos y voces, por separado | Código verificado; pesos y voces por verificar en Hugging Face | `LICENCIAS.md` |
| Motor de voz | Orquestador sin dependencias (sirve el Python 3.9 del Mac), trabajador por motor en entornos aislados, medidas objetivas, posproceso declarado, metadatos completos e índice CSV | `voz_harry/` |
| Interfaz local | Generar, escuchar y guardar WAV; motor, voz e idioma; velocidad y controles nativos; tono como posproceso; comparar, también a ciegas; valorar | `interfaz/index.html`, `voz_harry/servidor.py` |
| Instaladores | Entornos aislados por motor (Python 3.12 y cachés dentro de `05_voz_harry`); consulta de tamaños y licencias sin descargar; descarga solo con autorización | `instalar/` |
| Pruebas del software | 10 de 10 con Python 3.11, 3.12 y 3.13, con y sin numpy; gramática de 3.9 comprobada en los 23 archivos | `pruebas/test_voz.py` |

## 2. Audio real producido en la nube: solo prueba de la tubería

Para comprobar el recorrido completo con audio real usé **eSpeak NG**, el que trae el paquete `espeakng-loader` de PyPI. Recorrido: síntesis → WAV → metadatos → medidas → índice → interfaz → informe.

**No es un candidato:** es una voz de formantes, robótica. Su único valor es demostrar que la tubería funciona.

| Muestra | Audio | Síntesis | F0 mediana | Palabras/min |
|---|---|---|---|---|
| `espeak_prueba__es-419-m3__es__01` … `05` (español latinoamericano, variante masculina) | 8.0–11.0 s | 0.010–0.018 s | 103–109 Hz | 145–170 |
| `espeak_prueba__gmw-en-GB-x-rp-m3__en__06` (inglés británico RP) | 8.9 s | 0.014 s | 102 Hz | 181 |
| Una muestra generada desde la interfaz, texto 06, con velocidad 0.9 (nativa) y tono −2 semitonos (posproceso, ffmpeg rubberband) | 10.0 s | 0.028 s | 92 Hz | 162 |

Detalle completo en `evaluacion/comparacion_nube-linux-x86_64.md` y en el `.json` de cada muestra.

**Lo que comprobé:**
- archivos WAV PCM de 16 bits válidos;
- el espectrograma muestra formantes, armónicos y pausas en la puntuación;
- la F0 de YIN coincide con tonos sintéticos de 95, 120 y 210 Hz con un error del 0.3 %;
- el posproceso de tono lleva la F0 al valor esperado (±0.3 Hz con ffmpeg).

**No las escuché:** no puedo oír audio. Ninguna afirmación sobre cómo suenan sale de esta sesión.

**Defectos encontrados y corregidos durante la prueba:**
- eSpeak NG ignora rutas de datos de más de 230 caracteres y vuelve a la ruta con la que se compiló. Se resolvió con un enlace corto; en la Mac la ruta es corta.
- La voz británica de eSpeak se llama `gmw/en-GB-x-rp`, no `en-gb`.
- Un umbral de «poca voz» demasiado estricto para esta voz sintética.

## 3. Por qué empezar por Piper y Kokoro, si el preferido es Chatterbox

El razonamiento completo está en `investigacion/motores.md`. En resumen:
- **Peso.** Chatterbox pesa varios GB y exige tu autorización.
- **Referencia.** Su ventaja (el mismo timbre en los dos idiomas) depende de una grabación de referencia autorizada, que no existe.
- **Base de comparación.** Piper y Kokoro dan en minutos, y con menos de 500 MB, una línea base real en inglés británico y español mexicano.

## 4. Autorizaciones

1. **Red de esta sesión, o de la próxima.** Respuesta del custodio: no se habilita en esta sesión; lo hará en su Mac. Si quieres que genere y mida muestras de Piper y Kokoro en la nube, siempre etiquetadas como nube, añade en la configuración del entorno los dominios `huggingface.co`, `hf.co`, `cdn-lfs.huggingface.co`, `cdn-lfs.hf.co` y `cas-bridge.xethub.hf.co`. Si quieres un torch solo para CPU, más ligero, añade también `download.pytorch.org`.
2. **Chatterbox** (en la Mac o en la nube):
   - descargar los pesos de Multilingual V2: unos 3.2 GB, según mi estimación sin verificar;
   - opcionalmente, la V3, unos 2.1 GB más, o el modelo es-MX/Latam (tamaño por verificar);
   - el entorno de Python: unos 1.5–2 GB.

   El código es MIT. **La licencia de los pesos está por verificar.** Todo su audio lleva marca de agua Perth.

   Antes de descargar, `python3 -I instalar/consultar_modelos.py --motor chatterbox` te muestra los tamaños y la licencia exactos.

   **Respuesta del custodio (24-oct-2026, en esta sesión): autorizado, en la Mac y en la nube.** No se descargó en esta sesión porque Hugging Face sigue bloqueado, y el custodio decidió hacer en su Mac lo que necesita esa red.
3. **Grabaciones de referencia:** ninguna, salvo que tú registres alguna con el consentimiento expreso de la persona grabada.

## 5. Lo que falta, y dónde

Todo en la Mac (pasos en `README.md`):
1. `revisar_equipo.sh` y `consultar_modelos.py`: equipo real, tamaños y licencias exactos.
2. Piper y Kokoro: entornos, descargas, primera muestra comprobada y las seis pruebas.
3. **Tu escucha**, a ciegas si prefieres, y tu valoración en la interfaz.
4. Medidas del M4:
   - tiempo de síntesis, factor de tiempo real y memoria pico;
   - CPU frente a MPS en Kokoro.
5. Chatterbox, ya autorizado: V2 de PyPI y, después, V3 o es-MX.
6. Prueba sin conexión: con la red desconectada, una muestra por motor.
7. `voz.py informe` para el informe con mediciones del M4 y tu valoración.

**Nada de esto permite todavía declarar que la voz esté terminada ni validada en la Mac.**

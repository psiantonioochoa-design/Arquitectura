# Motores de voz: investigación (24-oct-2026)

**Cómo se hizo.** Desde una sesión de Claude Code en la nube cuya red permitía PyPI y `raw.githubusercontent.com`, pero **bloqueaba Hugging Face**.

- Leí los repositorios oficiales en GitHub y los metadatos y paquetes de PyPI.
- No pude leer las tarjetas de modelo, las listas de archivos ni las licencias de pesos alojadas en Hugging Face.
- Cada dato lleva su estado: **verificado** (fuente oficial leída hoy) o **por verificar**.
- Los datos por verificar se comprueban en la Mac con `instalar/consultar_modelos.py`, que solo lee metadatos y no descarga nada.

## Resumen

| | Chatterbox Multilingual | Kokoro-82M | Piper |
|---|---|---|---|
| Español | Sí, entre 23 idiomas (verificado). Hay un modelo específico **es-MX/Latam** (verificado que existe; archivos y licencia por verificar) | Sí, con fonetización eSpeak NG (`lang_code='e'`). Dos voces masculinas, calificadas **D** por su autor | Sí: **es_MX** (`ald`, `claude`), es_ES y es_AR |
| Inglés británico | El idioma `en` existe, pero el acento depende de la voz de referencia; la voz incluida no garantiza acento británico | **Sí: `bm_george`, `bm_fable` (C), `bm_lewis` (D+), `bm_daniel` (D)**, masculinas (verificado) | **en_GB**: `alan`, `northern_english_male` (norte, no sur), `vctk`, `semaine`, `aru`; la del sur es femenina |
| Misma voz en los dos idiomas | **Sí**, es su punto fuerte, pero con una grabación de referencia (ninguna autorizada) | Solo como experimento: voz británica + fonetización española | No: voces distintas por idioma |
| Edad 45–55, timbre medio-grave | Depende de la referencia; sin ella, de la voz incluida | Por escuchar | Por escuchar; VCTK son sobre todo jóvenes |
| Personalización del timbre | Clonación con referencia | Mezcla de voces (`'bm_george,bm_fable'`) | No |
| Expresividad | `exaggeration`, `cfg_weight`, `temperature` | Solo velocidad | `noise_scale`, `noise_w_scale` |
| Velocidad | No nativa (posproceso o `cfg_weight`) | `speed` | `length_scale` |
| Tamaño de los pesos | ~3.2 GB V2 (estimado) | ~330 MB (estimado) | 60–115 MB por voz (estimado) |
| Apple Silicon | `device='cpu'` o `'mps'` en el código (verificado); `torch==2.6.0` tiene rueda arm64 (verificado) | CPU; MPS con `PYTORCH_ENABLE_MPS_FALLBACK=1` según el README (verificado que lo dice) | CPU con onnxruntime; rueda arm64 verificada |
| Python | ≥3.10 (desarrollado en 3.11) | 3.10–3.12 | ≥3.9 (onnxruntime 1.31 pide ≥3.11) |
| Licencia del código | MIT (verificado) | Apache-2.0 (verificado) | GPL-3.0-or-later (piper1-gpl, verificado); la versión anterior, archivada, era MIT |
| Licencia de los pesos | Por verificar | Apache-2.0 según el README («Apache-licensed weights»); tarjeta por verificar | Una por voz, en su MODEL_CARD (por verificar) |
| Particularidad | **Marca de agua Perth** en todo el audio (verificado) | El español depende de eSpeak NG (GPL-3.0) | eSpeak NG integrado (GPL-3.0) |

## Por qué el orden de pruebas empieza por los motores ligeros

Chatterbox es el candidato preferido para la voz definitiva: es el único que puede sostener **el mismo timbre en español y en inglés**, tiene controles de expresividad y un modelo específico para el español de México. Aun así, conviene empezar por Piper y Kokoro, por cuatro razones:

1. **Recursos.**
   - Chatterbox pesa varios GB (unos 3.2 GB V2 más ~1.5–2 GB de entorno) y requiere tu autorización expresa.
   - Piper y Kokoro caben en menos de 500 MB y corren en CPU.
   - En una MacBook Air de 16 GB, que a veces tiene a Ollama cargado, eso importa.
2. **La ventaja de Chatterbox depende de algo que no tenemos.** Sostener una voz concreta en dos idiomas exige una grabación de referencia **autorizada**, y hoy no hay ninguna. Sin ella solo se puede oír su voz incluida (`conds.pt`), cuyo género, edad y acento están por escuchar.
3. **Base de comparación.** Piper y Kokoro dan en minutos una línea base real en los dos idiomas: británico (Kokoro `bm_*`, Piper `en_GB`) y mexicano (Piper `es_MX`). Con ella, la escucha de Chatterbox tiene un punto de comparación.
4. **Riesgo técnico.** Chatterbox fija `torch==2.6.0`, `transformers==5.2.0` y `gradio==6.8.0`, y la V3 solo está en el código de GitHub, no en PyPI. Es el motor con más probabilidad de problemas de instalación en macOS. Por eso va en su propio entorno, después de los otros.

**Orden propuesto en la Mac:**
1. Piper (`es_MX-claude-high`, `es_MX-ald-medium`, `en_GB-alan-medium`);
2. Kokoro (`bm_george`, `bm_fable`, `em_alex` y los experimentos);
3. con tu autorización, Chatterbox V2 de PyPI (voz incluida, `es` y `en`);
4. si lo autorizas, la V3 o el modelo es-MX.

## Chatterbox (Resemble AI)

- **Fuentes leídas** (rama `master`, 24-oct-2026):
  - `README.md` (SHA-256 `fd9315cc…`), `LICENSE` (`4248e910…`), `pyproject.toml` (`e1aab210…`) y `src/chatterbox/mtl_tts.py` (`93675904…`);
  - la rueda `chatterbox_tts-0.1.7-py3-none-any.whl` de PyPI (`83782500…`).
- **Modelos** (README):
  - Chatterbox-Turbo (350M) y Nano (110M): solo inglés;
  - Multilingual V3 (500M, 23 idiomas o más), recomendado;
  - el «Single Language Pack» con `Chatterbox-Multilingual-es-mx-latam`;
  - el Chatterbox original (inglés).
- **PyPI frente a GitHub:**
  - `chatterbox-tts` 0.1.7 de PyPI (subida el 26-mar-2026) solo descarga `t3_mtl23ls_v2.safetensors` (Multilingual V2);
  - el código de `master` acepta `t3_model="v3"`;
  - para V3 hay que instalar desde GitHub. `crear_entornos.sh --v3` fija el commit y lo anota.
- **Archivos de V2:** `ve.pt`, `t3_mtl23ls_v2.safetensors`, `s3gen.pt`, `grapheme_mtl_merged_expanded_v1.json`, `conds.pt` (la voz incluida) y `Cangjie5_TC.json`. Los tamaños están por verificar; mi estimación previa, sin comprobar, es de unos 3.2 GB en total.
- **Controles de `generate`:**
  - `exaggeration` (0.5), `cfg_weight` (0.5), `temperature` (0.8), `repetition_penalty`, `min_p` y `top_p`;
  - `audio_prompt_path` para clonar. Este proyecto solo lo permite con referencias autorizadas en el catálogo.
- **Marca de agua.** El README dice que todo audio lleva el watermarker Perth de Resemble AI, imperceptible y detectable.
- **Dispositivo.** El código carga con `map_location` para `cpu` y `mps`. El rendimiento en el M4 está por medir.

## Kokoro-82M (hexgrad)

- **Fuentes leídas** (`hexgrad/kokoro`, rama `main`):
  - `README.md` (`b50b8422…`), `LICENSE` Apache-2.0 (`c71d239d…`), `pyproject.toml` (`f8c3ae1c…`) y `kokoro/pipeline.py` (`499982bb…`);
  - **`kokoro.js/src/voices.js` (`7650e788…`)**, el catálogo de voces del autor;
  - `misaki` 0.9.4 (rueda de PyPI).
- **Voces británicas masculinas (verificado en `voices.js`):**

  | Voz | Calidad objetivo | Calificación general |
  |---|---|---|
  | `bm_george` | B | C |
  | `bm_fable` | B | C |
  | `bm_lewis` | C | D+ |
  | `bm_daniel` | C | D |

  Las cuatro existen. Que sus archivos `voices/<voz>.pt` estén hoy en Hugging Face está **por verificar** (bloqueado); `consultar_modelos.py` lo comprueba.
- **Voces en español.**
  - Están en el mismo archivo, comentadas: kokoro.js no las usa, pero la biblioteca de Python sí, con `lang_code='e'`.
  - `em_alex` (D) y `em_santa` (D) son masculinas; `ef_dora` (D), femenina.
  - El nombre de `em_santa` sugiere una voz de personaje: hay riesgo de teatralidad.
  - La fonetización es la del eSpeak NG `es`, sin variante mexicana declarada.
- **API.**
  - `KPipeline(lang_code, repo_id, device)` y `pipeline(texto, voice=…, speed=…)`;
  - la mezcla de voces con comas promedia los estilos;
  - audio a 24 kHz.
- **Apple Silicon.** El README dice: «On Mac M1/M2/M3/M4 devices, you can explicitly specify … `PYTORCH_ENABLE_MPS_FALLBACK=1` to enable GPU acceleration». No está medido.
- **spaCy.** `misaki` descarga `en_core_web_sm` en el primer uso si falta. `crear_entornos.sh kokoro` lo instala de antemano, para que todo funcione sin conexión.

## Piper (OHF-Voice / rhasspy)

- **Fuentes leídas:**
  - `OHF-Voice/piper1-gpl`: `README.md` (`a73f5760…`), `docs/VOICES.md` (`cc724e58…`) y `COPYING` GPL-3.0 (`0ae0485a…`);
  - `rhasspy/piper` (archivado): `VOICES.md` (`4ce53d3b…`), con los enlaces de cada voz a `rhasspy/piper-voices@v1.0.0`, y `LICENSE.md` MIT;
  - la rueda `piper_tts-1.8.0-cp39-abi3-macosx_11_0_arm64.whl` (`33e74259…`).
- **API de piper-tts 1.8.0** (instalada y verificada en la nube):
  - `PiperVoice.load(model_path, config_path=None, use_cuda=False, …)` y `PiperVoice.synthesize(texto, syn_config)`, que produce fragmentos con `audio_float_array` y `sample_rate`;
  - `SynthesisConfig(speaker_id, length_scale, noise_scale, noise_w_scale, normalize_audio, volume)`.
- **Inglés británico (en_GB):**
  - `alan` (low y medium);
  - `alba`, `cori`, `jenny_dioco` y `southern_english_female`, por sus nombres femeninas;
  - `northern_english_male` (medium), masculina pero del **norte** de Inglaterra;
  - `vctk`, `semaine` y `aru`, de varios hablantes.

  **No hay una voz masculina del sur de Inglaterra declarada como tal.**
  - La región y el género de `alan` no están en la lista: hay que mirar su MODEL_CARD.
  - Las de varios hablantes pueden incluir hombres del sur (VCTK registra el acento de cada hablante), pero son voces de corpus, mayoritariamente jóvenes.
- **Español de México (es_MX):** `ald` (medium) y `claude` (high). Su género no está en la lista: hay que mirar la MODEL_CARD o escucharlas. Hay también es_ES (`carlfm`, `davefx`, `mls_*`, `sharvard`) y es_AR (`daniela`).
- **Licencias de las voces.** Según `docs/VOICES.md`: «The `MODEL_CARD` file for each voice contains important licensing information … Some voices may have restrictive licenses». `descargar_modelos.py` guarda la MODEL_CARD junto a cada voz.

## Lo que queda por verificar (en la Mac, con red)

1. Tamaños exactos, SHA-256 y licencias de los pesos: `python3 -I instalar/consultar_modelos.py`.
2. Que existan `voices/bm_george.pt`, `bm_daniel.pt`, `bm_lewis.pt`, `bm_fable.pt`, `em_alex.pt` y `em_santa.pt` en `hexgrad/Kokoro-82M`.
3. El género, el acento y la licencia de `en_GB-alan`, `es_MX-claude` y `es_MX-ald`, en sus MODEL_CARD.
4. Los archivos y la licencia de `ResembleAI/Chatterbox-Multilingual-es-mx-latam`, y si los carga `from_local` o necesita otra API.
5. MPS frente a CPU en Kokoro y Chatterbox: tiempos y memoria medidos con `voz.py generar --dispositivo mps`.

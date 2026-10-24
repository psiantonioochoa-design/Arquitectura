# 05_voz_harry · Voz local de Harry (texto a audio)

> **Estado al 24-oct-2026: tubería, interfaz e instaladores listos y probados en la nube; todavía sin audio de los motores candidatos.**
>
> La sesión que construyó esto corría en la nube (Linux x86_64, sin GPU) y su red bloqueaba Hugging Face, donde están los pesos de Piper, Kokoro y Chatterbox.
>
> Las únicas muestras reales son de **eSpeak NG**, un motor de prueba que solo comprueba la tubería de punta a punta: **no es candidato para la voz de Harry**.
>
> Faltan, y solo pueden hacerse en tu Mac:
> - las muestras de Piper, Kokoro y Chatterbox;
> - las mediciones del M4;
> - la valoración auditiva.

**Qué es y qué no es:**
- Convierte en audio el texto que recibe. **No razona, no genera texto y no conoce la identidad de Harry:** no importa el núcleo (`06_implementacion`) ni lee la constitución.
- No usa micrófono, no escucha de forma permanente, no se integra con Nimbo y no crea servicios persistentes.
- La interfaz solo es accesible desde el propio equipo (`127.0.0.1`).
- Los seis textos de prueba (`configuracion/textos_prueba.json`) son material de comparación acústica, no respuestas aprobadas de Harry.
- La edad vocal de 45–55 años es una característica sonora buscada, no una biografía.

## Estructura

```
05_voz_harry/
├── voz.py                         línea de órdenes (sirve el python3 del sistema, 3.9)
├── voz_harry/                     paquete
│   ├── cli.py, servidor.py, cliente.py, generar.py, informe.py, catalogo.py, equipo.py, rutas.py   (solo biblioteca estándar)
│   ├── trabajador.py              corre DENTRO del entorno de cada motor; mide tiempos, memoria y audio
│   ├── audio.py, postproceso.py   WAV, medidas (F0 por YIN, nivel, silencios, ritmo), posproceso declarado
│   └── motores/                   piper, kokoro, chatterbox, espeak_prueba (prueba de tubería), seno_prueba (pruebas)
├── interfaz/index.html            interfaz local: generar, escuchar, guardar, comparar (también a ciegas) y valorar
├── configuracion/
│   ├── catalogo.json              motores, voces, controles nativos, licencias y estado de verificación de cada dato
│   └── textos_prueba.json         los 6 textos literales
├── instalar/
│   ├── revisar_equipo.sh          solo lee: sistema, memoria, disco, Python, ffmpeg y pesos que ya existan
│   ├── crear_entornos.sh          un entorno aislado por motor en entornos/<motor> (Python 3.12, cachés dentro de 05_voz_harry)
│   ├── consultar_modelos.py       tamaños y licencias en Hugging Face, sin descargar
│   ├── descargar_modelos.py       descarga solo con --autorizo (y --autorizo-grande para Chatterbox)
│   └── requisitos/                versiones fijadas por motor
├── muestras/<equipo>/             WAV + JSON por muestra e indice.csv, separados por el equipo que los generó
├── evaluacion/                    comparacion_<equipo>.md y valoraciones.csv (las tuyas)
├── investigacion/motores.md       fuentes, voces, compatibilidad y orden de pruebas
├── LICENCIAS.md                   código, pesos y voces, por separado
├── INFORME_voz.md                 qué se hizo, con qué evidencia y qué falta
└── pruebas/test_voz.py            pruebas del software (sin modelos ni red)
```

`entornos/`, `modelos/` y `.cache/` no se versionan: se crean en cada equipo.

## En tu Mac, paso a paso

Todas las órdenes van desde esta carpeta:

```bash
cd /Volumes/NOUS/QUINTA_IDENTIDAD/05_voz_harry
```

### 1. Ver el equipo y las licencias (no cambia nada)

```bash
bash instalar/revisar_equipo.sh
```

```bash
python3 -I instalar/consultar_modelos.py
```

La segunda orden muestra el tamaño exacto y la licencia declarada de cada archivo. Las voces de Piper tienen además su licencia en la MODEL_CARD.

### 2. Piper, el más ligero (unos 60–115 MB por voz)

```bash
bash instalar/crear_entornos.sh piper
```

```bash
python3 -I instalar/descargar_modelos.py --motor piper --voz es_MX-claude-high --voz es_MX-ald-medium --voz en_GB-alan-medium --voz en_GB-northern_english_male-medium --autorizo
```

Primera muestra real, comprobada:

```bash
python3 -I voz.py muestra --motor piper --voz es_MX-claude-high --idioma es
```

Las seis pruebas, en las combinaciones compatibles:

```bash
python3 -I voz.py generar --motor piper
```

### 3. Kokoro (unos 330 MB de pesos más el entorno con torch)

```bash
bash instalar/crear_entornos.sh kokoro
```

```bash
python3 -I instalar/descargar_modelos.py --motor kokoro --autorizo
```

```bash
python3 -I voz.py muestra --motor kokoro --voz bm_george --idioma en
```

```bash
python3 -I voz.py generar --motor kokoro
```

Para comparar con la GPU (MPS), por medir:

```bash
python3 -I voz.py generar --motor kokoro --dispositivo mps
```

### 4. Chatterbox (autorizado por el custodio el 24-oct-2026; varios GB)

Mira antes el tamaño y la licencia con `consultar_modelos.py --motor chatterbox`.

```bash
bash instalar/crear_entornos.sh chatterbox --autorizo-grande
```

```bash
python3 -I instalar/descargar_modelos.py --motor chatterbox --variante v2 --autorizo --autorizo-grande
```

```bash
python3 -I voz.py muestra --motor chatterbox --voz predeterminada --idioma es
```

```bash
python3 -I voz.py generar --motor chatterbox
```

- **Multilingual V3:** `crear_entornos.sh chatterbox --v3 --autorizo-grande` en un entorno nuevo, y después `--variante v3` al descargar y al generar.
- **Voz de referencia:** solo con una grabación autorizada y registrada en `configuracion/catalogo.json`.

### 5. Escuchar, comparar y valorar

```bash
python3 -I voz.py interfaz --abrir
```

En la interfaz:
- **Generar:** escribe o elige un texto, el motor, la voz y el idioma, y ajusta la velocidad, los controles del motor y el tono.
- **Comparar:** filtra por prueba, idioma y equipo; con «Escucha a ciegas» se ocultan motor y voz.
- **Valorar:** cada valoración se guarda en `evaluacion/valoraciones.csv`.

Al cerrar con Ctrl-C se detienen también los procesos de los motores.

### 6. Informe

```bash
python3 -I voz.py informe
```

Escribe `evaluacion/comparacion_<equipo>.md`, con las mediciones objetivas en una sección y tu valoración auditiva en otra.

### 7. Funcionamiento sin conexión

Los motores corren siempre con `HF_HUB_OFFLINE=1`: si falta un peso, fallan en vez de descargarlo. Para comprobarlo de verdad, desconecta la red y repite el paso de la primera muestra con cada motor.

## Controles: nativos y posproceso

| Control | Piper | Kokoro | Chatterbox | Cómo se aplica |
|---|---|---|---|---|
| Velocidad | `length_scale` | `speed` | No nativa | Nativa donde existe; en Chatterbox, posproceso **declarado** en los metadatos |
| Expresividad | `noise_scale`, `noise_w_scale` | — | `exaggeration`, `cfg_weight`, `temperature` | Nativa |
| Timbre | — | Mezcla de voces (`'bm_george,bm_fable'`) | Voz de referencia (ninguna autorizada) | Nativa |
| Tono (semitonos) | — | — | — | **Posproceso**: ffmpeg rubberband con formantes preservados si existe; si no, otro método, que queda anotado |

Cada muestra guarda `controles_nativos` y `posproceso` por separado en su `.json`.

## Medidas de cada muestra

Las medidas objetivas son:
- tiempo de síntesis, factor de tiempo real y si la síntesis incluyó la carga del modelo;
- memoria pico del proceso del motor (en macOS, además, el RSS actual con `ps` y, si se usa MPS, la memoria de Metal);
- duración, nivel y silencios;
- **F0** (tono fundamental), mediana y percentiles 10 y 90;
- palabras por minuto;
- el **equipo real** que la generó.

**No son medidas objetivas** la naturalidad, la calidez, la edad aparente, el acento ni la expresividad. Esas te toca juzgarlas a ti, escuchando.

## Pruebas del software

```bash
python3 -I -m unittest discover -s pruebas
```

Con numpy, que traen los entornos de los motores:

```bash
entornos/piper/bin/python -I -m unittest discover -s pruebas
```

Verifican:
- que los textos sean literales;
- la coherencia del catálogo;
- que no haya dependencia de la identidad ni del razonamiento;
- que no haya micrófono ni red abierta;
- las medidas y el posproceso;
- el protocolo del trabajador;
- las defensas de la interfaz.

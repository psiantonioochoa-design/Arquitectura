# Licencias: código, pesos y voces, por separado

Estado al 24-oct-2026. **Verificado** quiere decir leído hoy en la fuente oficial (ver `investigacion/motores.md`). **Por verificar** quiere decir que la fuente está en Hugging Face, inaccesible desde la sesión en la nube; se comprueba en la Mac con `python3 -I instalar/consultar_modelos.py` y leyendo la MODEL_CARD que `descargar_modelos.py` guarda junto a cada voz de Piper.

## Motores (código)

| Componente | Licencia | Estado | Observación |
|---|---|---|---|
| `piper-tts` 1.8.0 (OHF-Voice/piper1-gpl) | GPL-3.0-or-later | Verificado (PyPI y `COPYING`) | Uso local y personal sin problema. Si algún día se distribuyera un programa que lo integre, ese programa tendría que cumplir la GPL |
| Piper anterior (rhasspy/piper, archivado) | MIT | Verificado | No se usa |
| eSpeak NG (dentro de `piper-tts`, de `espeakng-loader` y usado por `misaki` para el español) | GPL-3.0 | Verificado (licencia conocida del proyecto; la de `espeakng-loader` en PyPI está vacía) | Mismo comentario que Piper |
| `kokoro` 0.9.4 | Apache-2.0 | Verificado (`LICENSE`) | — |
| `misaki` 0.9.4 | Apache-2.0 | Verificado (metadatos de PyPI) | — |
| `chatterbox-tts` 0.1.7 y su código en GitHub | MIT | Verificado (`LICENSE`) | — |
| `resemble-perth` (marca de agua) | Por verificar (PyPI no declara licencia) | Por verificar | Chatterbox lo aplica a **todo** el audio que genera |
| `torch` 2.6.0 | BSD-3-Clause | Verificado (PyPI) | — |
| `onnxruntime` 1.31.0 | MIT | Verificado (PyPI) | — |
| `numpy`, `soundfile`, spaCy y `en_core_web_sm` | BSD / MIT (según sus proyectos) | Por verificar en esta sesión | — |
| Este paquete (`voz_harry/`, `interfaz/`, `instalar/`) | Del proyecto del custodio | — | No integra código de los motores: los llama en procesos aparte |

## Pesos

| Pesos | Licencia | Estado |
|---|---|---|
| Kokoro-82M (`hexgrad/Kokoro-82M`) | Apache-2.0 según el README del código («Apache-licensed weights») | Tarjeta del modelo por verificar |
| Chatterbox (`ResembleAI/chatterbox`) y `Chatterbox-Multilingual-es-mx-latam` | Por verificar | Por verificar; no se descarga sin tu autorización |

## Voces

| Voces | Licencia | Estado |
|---|---|---|
| Kokoro: `bm_*`, `em_*` | Las del repositorio de pesos | Por verificar con la tarjeta |
| Piper: `en_GB-*`, `es_MX-*`, `es_ES-*` | **Una por voz**, en su MODEL_CARD. El aviso oficial dice que algunas pueden ser restrictivas | Por verificar voz por voz antes de elegir una |
| Chatterbox: voz incluida (`conds.pt`) | Las de los pesos | Por verificar |
| Voces de referencia para clonar | Solo grabaciones con **consentimiento expreso** de la persona grabada, registradas en `configuracion/catalogo.json` | **Ninguna autorizada.** No se imitan actores ni personas reconocibles |

## Reglas que aplica el código

- `descargar_modelos.py` no descarga sin `--autorizo`, y Chatterbox exige además `--autorizo-grande`. Antes de descargar muestra tamaño y licencia, y pide confirmación.
- El adaptador de Chatterbox se niega a usar como referencia un archivo que no esté en `referencias_de_voz_autorizadas`.
- Cada muestra guarda en sus metadatos el motor, la versión y los controles usados, para poder rastrear su licencia.

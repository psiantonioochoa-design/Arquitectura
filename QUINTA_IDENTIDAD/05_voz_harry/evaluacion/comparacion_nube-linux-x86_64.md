# Comparación de voces · equipo `nube-linux-x86_64`

Generado: 2026-10-24T22:33:40. Equipo: Linux 6.18.44-fc-v153, Intel(R) Xeon(R) Processor @ 2.10GHz, 15.7 GB, GPU: no detectada.

> Medido en la nube: NO es una medición de la MacBook Air M4.

## 1. Mediciones objetivas

Tiempos de síntesis medidos de pared en el trabajador. La primera muestra de cada voz incluye cargarla. La memoria es el pico del proceso del motor desde que arrancó: incluye el modelo. F0 es el tono fundamental (YIN) en tramos con voz; describe la altura de la voz, no su timbre ni su calidez.

| Motor | Voz | Idioma | Prueba | Audio (s) | Síntesis (s) | Factor t. real | Memoria pico (MB) | F0 mediana (Hz) | F0 p10–p90 | Palabras/min | Posproceso |
|---|---|---|---|---|---|---|---|---|---|---|---|
| espeak_prueba | es-419+m3 | es | 01 | 8.01 | 0.018 * | 0.002 | 40.8 | 104.6 | 92.8–115.9 | 150.0 | no |
| espeak_prueba | es-419+m3 | es | 02 | 9.709 | 0.01 | 0.001 | 47.0 | 108.1 | 98.2–115.9 | 167.0 | no |
| espeak_prueba | es-419+m3 | es | 03 | 9.529 | 0.012 | 0.001 | 47.2 | 103.2 | 96.4–115.0 | 170.2 | no |
| espeak_prueba | es-419+m3 | es | 04 | 11.029 | 0.015 | 0.001 | 48.7 | 108.8 | 97.0–117.6 | 147.0 | no |
| espeak_prueba | es-419+m3 | es | 05 | 9.952 | 0.01 | 0.001 | 48.7 | 107.4 | 97.6–116.8 | 144.9 | no |
| espeak_prueba | gmw/en-GB-x-rp+m3 | en | 06 | 8.943 | 0.014 * | 0.002 | 41.9 | 101.9 | 82.3–119.4 | 181.2 | no |

\* incluye la carga de la voz o del modelo en esa primera síntesis.

### Resumen por voz

| Motor | Voz | Muestras | Factor t. real (mediana, sin primeras) | Memoria pico máx. (MB) | F0 mediana ES (Hz) | F0 mediana EN (Hz) |
|---|---|---|---|---|---|---|
| espeak_prueba | es-419+m3 | 5 | 0.001 | 48.7 | 107.4 | — |
| espeak_prueba | gmw/en-GB-x-rp+m3 | 1 | — | 41.9 | — | 101.9 |

Una F0 parecida en español y en inglés para la misma voz es solo un indicio de consistencia; el timbre se juzga escuchando.

## 2. Valoración auditiva del custodio

**Todavía no hay valoraciones de estas muestras.** Ninguna afirmación sobre naturalidad, calidez, edad aparente, acento o expresividad se puede hacer sin escuchar. Valóralas en la interfaz (`python3 voz.py interfaz`), de preferencia con la escucha a ciegas.


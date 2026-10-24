# Documento de continuidad · 24-oct-2026

Escrito al retomar el proyecto en una sesión nueva de Claude Code, antes de modificar nada, y actualizado al cerrar la sesión. Separa:
- lo que **verifiqué** en los archivos;
- lo que **solo consta** en informes o en el mensaje del custodio;
- lo que **funciona** y con qué evidencia;
- lo **pendiente**;
- las **autorizaciones** vigentes;
- lo que **solo puede hacerse en la Mac**.

## 1. Dónde se trabajó y qué se recibió

- **Equipo de esta sesión.** Contenedor en la nube: Linux x86_64 (Ubuntu 24.04), 4 vCPU Intel Xeon a 2.10 GHz, 15.7 GB, sin GPU. Python 3.11, 3.12 y 3.13 (no 3.9).
- **Red.** Permitidos PyPI y `raw.githubusercontent.com`. **Denegados:** `huggingface.co` (y su CDN), `download.pytorch.org` y `github.com`.
- **Sin acceso** a la Mac, al SSD NOUS, a Ollama ni a los modelos.
- **Lo recibido.** El repositorio de la sesión (`Arquitectura`) contiene la tesis de arquitectura del custodio, no este proyecto. El proyecto llegó como **`Copia_de_QUINTA_IDENTIDAD.zip`**, adjuntado por el custodio:
  - 426 entradas, incluidas las de `__MACOSX`, unos 15 MB descomprimido;
  - se extrajo sin modificar en una carpeta aparte;
  - las reparaciones se hicieron sobre una copia, con un control de versiones local cuya primera versión es el estado recibido.
- **No venían en el ZIP:**
  - `05_voz_harry/`, que no existía;
  - un informe de la etapa 3 y `CAMBIOS_instrucciones.md`, que la 0.2 citaba y no existía;
  - pesos de modelos, que no hacían falta.
- **Publicación.** Por decisión expresa del custodio (24-oct-2026), el proyecto completo se sube a la rama `claude/quinta-identidad-harry-continuity-uu0lan` del repositorio `Arquitectura`, que es **público**. Se le advirtió antes que eso incluye la constitución y el borrador clínico del Anexo A.
- **No se buscó nada fuera del proyecto.** La búsqueda en Google Drive se limitó a nombres de archivos del proyecto y no encontró nada pertinente.

## 2. Lo que verifiqué en los archivos

| Carpeta | Contenido verificado | Cómo |
|---|---|---|
| `00_directriz/` | Directriz maestra y su procedencia. El SHA-256 del cuerpo coincide con el registrado | Prueba `test_directriz_coincide_con_su_procedencia`, que pasa |
| `01_investigacion/`, `02_comparacion/`, `03_sintesis/` | Los 12 documentos existen (6 + 3 + 3). La recuperación indexa los que el corpus declara (dossiers, matriz, hipótesis, arquitectura); resoluciones, conflictos y coherencia quedan excluidos por contener situaciones de prueba | Listado e índice. **Leí completos** el README raíz, la directriz, la procedencia, los informes de las etapas 1 y 2, el README de implementación, `05_pruebas/00_conjunto_de_pruebas.md` y el Art. 8 de la constitución. Del resto de la constitución y del Anexo A leí partes (Arts. 6, 9, 12.3, 13.3–13.4, 14 C5; A.5). **La investigación (01–03) no la releí** |
| `04_constitucion/` | Constitución de Harry 1.0 («propuesta… **No aprobada todavía**»), Anexo A («**en revisión, no aprobado**»), Anexo B, las dos revisiones, `CAMBIOS.md` y las versiones archivadas `umbral_1.0/` y `nell_1.0/` | Encabezados y `aprobaciones.json` |
| `05_pruebas/` | Metodología (rúbrica 0–2, criterios, M-1 a M-10), 92 casos, CSV y generador | `harry.py validar`: 92 casos válidos e iguales al generador; 69 de un turno, 18 multiturno, 5 pares; 17 pendientes del Anexo A |
| `06_implementacion/` | Código, configuración, instrucciones 0.1 y 0.2, plataformas `ollama_*` (bloqueadas) y `piloto_*` (con `permitir_conversaciones_reales: true` y puerto 11435), registro de recursos, matriz, 32 pruebas, README e informes de las etapas 1 y 2 | Lectura del código y las configuraciones; pruebas corridas |
| `07_evaluaciones/` | Cuatro simulaciones técnicas (tres de la etapa 1 y una de la etapa 2). `exploratorias/` y `conformidad/` vacías | Listado |

**Estado de la etapa 3 tal como llegó** (pruebas corridas sin tocar nada):
- **32 pruebas: 4 fallos y 1 error**, lo que confirma «cinco pruebas fallaban»;
- el generador de la matriz apuntaba a `harry_borrador_0.1.md`;
- no había registro de cambios, calibración ni prefiltro;
- no había ninguna corrida exploratoria.

Coincide con lo reportado.

## 3. Lo que solo consta en informes o en el mensaje del custodio

No lo pude comprobar desde aquí:
- **Inventario de la Mac** (`INFORME_etapa_1.md`): el ejecutable de Ollama en `local-statistical-ai/proyecto/work/ollama/ollama`, los modelos `qwen3.5:latest` (6.55 GB) y `qwen3:8b`, y la memoria al 46 %.
- **Equipo de destino:** MacBook Air **M4**, **16 GB**, **Ollama 0.35.1**. Solo en el mensaje del custodio; los archivos solo mencionan «16 GB» en un comentario del adaptador.
- **Las pruebas** pasaban 32 de 32 antes de la etapa 3, con Python 3.9.6 y 3.13.12 (informe de la etapa 2).
- **El resumen de la etapa 3:** instrucciones 0.2, registro de recursos, investigación bajo demanda, plataformas piloto, cinco pruebas fallando, sin Ollama ni conversaciones reales. Solo en el mensaje del custodio, porque la sesión se interrumpió sin informe. Lo que sí pude comprobar en los archivos coincide.
- **La autorización del piloto:** la descripción de las plataformas `piloto_*` dice «Autorizado por el custodio el 24-oct-2026 solo para conversaciones sintéticas», y el mensaje del custodio la confirma.

## 4. Lo que funciona y con qué evidencia (al cerrar esta sesión)

| Qué | Evidencia | Límite |
|---|---|---|
| Pruebas del software de Harry | **51 de 51** con Python 3.11, 3.12 y 3.13 | Falta correrlas con el 3.9.6 de la Mac; la gramática de 3.9 está comprobada |
| Matriz de trazabilidad contra la 0.2 | 84 requisitos sin inconsistencias; la de la 0.1, archivada | — |
| Ni rúbricas ni respuestas modelo llegan al modelo | Pruebas sobre el contexto completo de los 92 casos. Se encontró y corrigió una fuga real de ejemplos resueltos (8.4 y la tabla de 13.3) en 7 casos | Ver `06_implementacion/INFORME_etapa_3.md` §2.1 |
| Calibración, prefiltro y comparación | Pruebas del software y ensayo con un servidor simulado | Sin datos reales todavía |
| Guion del piloto | Ensayado de punta a punta contra un **Ollama simulado** | Prueba el guion, no la Mac |
| Contextos que recibirá cada modelo en el piloto | Simulación técnica registrada: media de 4,614 y máximo de 4,822 tokens estimados, de 7,168 disponibles | Estimación sin tokenizador |
| Tubería de voz e interfaz | Audio real con el motor de **prueba** eSpeak NG (6 textos y 2 muestras más); interfaz probada en Chromium; servidor solo en 127.0.0.1 | **Ningún motor candidato produjo audio**: Hugging Face bloqueado |
| Pruebas del software de la voz | 10 de 10 con Python 3.11, 3.12 y 3.13 | — |

## 5. Pendiente o fallando

1. **El piloto con modelos reales no se ejecutó.** Está preparado: `06_implementacion/piloto/`.
2. **No hay voz candidata con audio:**
   - Piper, Kokoro y Chatterbox: pesos sin descargar;
   - sin mediciones del M4;
   - sin tu escucha.
3. **Decisiones del custodio:**
   - aprobar la constitución, el Anexo A, los umbrales, el conjunto de pruebas y las instrucciones;
   - las seis decisiones de `06_implementacion/INFORME_etapa_3.md` §7, entre ellas la frase del Anexo A dentro de I-10 y la exclusión de ejemplos;
4. **`aprobaciones.json`** registra las instrucciones como «borrador 0.1». Solo lo edita el custodio.
5. **Investigación** (`01_investigacion/fuentes.md`): los pendientes menores que ya constaban.

## 6. Autorizaciones vigentes

| Autorización | Fuente | Alcance |
|---|---|---|
| Etapas 1 y 2 de la construcción técnica | Informes de las etapas 1 y 2 | Infraestructura, instrucciones en borrador, recuperación, sesiones, matriz, tipos de corrida |
| **Piloto exploratorio** | Mensaje del custodio (24-oct-2026) y descripción de las plataformas `piloto_*` | Conversaciones **sintéticas**, **un modelo a la vez**, 15 casos independientes del Anexo A, dos repeticiones por modelo |
| **Voz local** | Mensaje del custodio (24-oct-2026) | Texto a audio local en español e inglés británico, interfaz local, muestras |
| Descargar modelos grandes | **Autorizado** por el custodio en esta sesión (24-oct-2026), después de ver la estimación de tamaños y el estado de las licencias | Chatterbox, en la Mac y en la nube. No se descargó aquí: Hugging Face sigue bloqueado y el custodio decidió no habilitarlo en esta sesión |
| Grabaciones de referencia | **Ninguna** | — |
| **No autorizado** | Mensaje del custodio y README | Entrenamiento, personas reales, cambios en Nimbo, micrófono, escucha permanente, servicios persistentes, interfaces expuestas a internet. **Nada está aprobado** en `aprobaciones.json` |

## 7. Lo que exige la Mac

La lista concreta está en **`PENDIENTES_MAC.md`**.

## 8. Lo que hizo esta sesión

- **Etapa 3:** `06_implementacion/INFORME_etapa_3.md` y `configuracion/instrucciones/CAMBIOS_instrucciones.md`.
- **Voz:** `05_voz_harry/INFORME_voz.md`, `README.md`, `LICENCIAS.md` e `investigacion/motores.md`.
- **Parche** contra el ZIP recibido: `CAMBIOS_etapa3_y_voz.patch`, en la entrega.

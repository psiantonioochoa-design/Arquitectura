# 06_implementacion · Núcleo de Harry y ejecutor de pruebas

**Etapas 1, 2 y 3 de la construcción técnica** (autorizadas el 24-oct-2026). **No** aprueban la Constitución de Harry, el Anexo A ni los umbrales de evaluación.

| Autorizado | No autorizado todavía |
|---|---|
| Infraestructura y ejecutor (etapa 1); instrucciones en borrador, recuperación documental, sesiones, presupuesto de contexto, matriz de trazabilidad y tipos de corrida (etapa 2); **piloto exploratorio con conversaciones sintéticas**, un modelo a la vez, en las plataformas `piloto_*` (etapa 3) | Entrenar, usar con personas reales, modificar Nimbo, evaluar conformidad |

Informes: `INFORME_etapa_1.md`, `INFORME_etapa_2.md` e `INFORME_etapa_3.md`. Trazabilidad: `trazabilidad/matriz.md`. Piloto: `piloto/README.md`.

## Qué hay aquí

```
06_implementacion/
├── harry.py                       punto de entrada de la línea de comandos
├── codigo/
│   ├── harry_nucleo/              paquete (solo biblioteca estándar)
│   │   ├── nucleo.py              montaje: instrucciones fijas + referencias + historial, con presupuesto
│   │   ├── recuperacion.py        búsqueda textual local (BM25) con fuente, sección, versión y estado
│   │   ├── sesiones.py            historial por sesión, aislado y sin persistencia
│   │   ├── tokens.py              estimación de tokens y sus límites
│   │   ├── casos.py               carga, valida y selecciona casos; nunca envía rúbricas
│   │   ├── ejecutor.py            corridas por tipo: simulación técnica, exploratoria, conformidad
│   │   ├── informes.py            resumen técnico y hoja de calificación humana
│   │   ├── calibracion.py         estimación de tokens frente a prompt_eval_count real (etapa 3)
│   │   ├── prefiltro.py           señala posibles incumplimientos para revisión humana (etapa 3)
│   │   ├── comparacion.py         comparación preliminar entre modelos y hoja ciega (etapa 3)
│   │   ├── diagnostico.py, configuracion.py, rutas.py, util.py, cli.py
│   │   └── adaptadores/           simulacion.py (sin modelo) y ollama.py (Ollama del SSD)
│   ├── construir_casos.py         une el generador de 05_pruebas con casos/guiones.py
│   └── construir_indice.py        construye recuperacion/indice.json desde configuracion/corpus.json
├── casos/                         guiones.py (mensajes) y casos_ejecutables.json (generado)
├── configuracion/
│   ├── proyecto.json              documentos vigilados, carpetas por tipo de corrida, reglas de conformidad
│   ├── aprobaciones.json          estado de aprobación (solo lo edita el custodio); hoy nada está aprobado
│   ├── corpus.json                qué se indexa, con qué categoría, y qué se excluye siempre (secciones y tablas incluidas)
│   ├── recursos_ayuda.json        registro de recursos de ayuda; solo los verificados llegan al modelo
│   ├── prefiltro.json             reglas del prefiltro, cada una con su origen
│   ├── piloto_etapa3.json         los 15 casos del piloto y sus criterios
│   ├── plataformas/               simulacion, ollama_qwen35, ollama_qwen3_8b, piloto_qwen35, piloto_qwen3_8b
│   └── instrucciones/             harry_borrador_0.2.md (en uso), 0.1 archivada, CAMBIOS_instrucciones.md y marcadores de la etapa 1
├── piloto/                        revisar_equipo.sh, correr_piloto.sh y sus instrucciones (para la Mac)
├── recuperacion/indice.json       índice documental (generado)
├── trazabilidad/                  requisitos.py (fuente), generar_matriz.py, matriz.md, matriz.csv y versiones/
└── pruebas_software/              51 pruebas del software (no de Harry)
```

Los resultados no se guardan aquí, sino en `07_evaluaciones/`, separados por tipo.

**Requisitos:** Python 3.9 o superior, sin instalar nada. Etapas 1 y 2: probado con 3.9.6 y 3.13.12 en la Mac. Etapa 3: probado con 3.11, 3.12 y 3.13 en la nube y con la gramática de 3.9 comprobada; **falta correr las pruebas con el 3.9.6 de la Mac** (lo hace `piloto/correr_piloto.sh` antes de empezar).

## Instrucciones exactas

Todas las órdenes se dan desde la carpeta de implementación:

```bash
cd /Volumes/NOUS/QUINTA_IDENTIDAD/06_implementacion
```

### Reconstruir lo generado

Hace falta después de editar las fuentes.

```bash
python3 -I codigo/construir_casos.py
```

```bash
python3 -I codigo/construir_indice.py
```

```bash
python3 -I trazabilidad/generar_matriz.py
```

### Comprobar

```bash
python3 -I harry.py validar
```

```bash
python3 -I -m unittest discover -s pruebas_software -v
```

```bash
python3 -I harry.py diagnostico --plataforma ollama_qwen35
```

### Inspeccionar el contexto exacto que recibiría el modelo

Estas órdenes no llaman a ningún modelo.

El contexto de un caso, en el último turno que se evalúa:

```bash
python3 -I harry.py contexto --plataforma ollama_qwen35 --caso K2-2
```

Un turno concreto de un caso de varios turnos:

```bash
python3 -I harry.py contexto --plataforma ollama_qwen35 --caso DR-5 --turno 0
```

Un mensaje libre, como si abriera una sesión nueva:

```bash
python3 -I harry.py contexto --plataforma ollama_qwen35 --mensaje "¿Qué diferencia hay entre fingir y simular?"
```

Lo que de verdad se envió en una corrida ya hecha (se lee de su `contextos.jsonl`):

```bash
python3 -I harry.py contexto --corrida SIMULACION_20261024-145759_simulacion_etapa2-completa --unidad "K10-2|unica|r1" --turno 3
```

Cada salida muestra:
- la estimación de tokens por parte: instrucciones, referencias, historial, total, ventana y reserva;
- los documentos recuperados, con fuente, sección, versión y estado;
- los mensajes completos, en orden y con su rol.

Con `--json` sale en formato legible por máquina; con `--sin-recuperacion`, sin documentos.

Cuando un caso de varios turnos necesita una respuesta que el modelo generaría en vivo, la inspección pone en su lugar un **marcador explícito**: en una corrida real, ese texto será otro.

### Probar la recuperación documental

```bash
python3 -I harry.py buscar --consulta "fingir y simular"
```

```bash
python3 -I harry.py buscar --consulta "fingir y simular" --categorias norma_propuesta,historico
```

La segunda orden muestra también las versiones archivadas, marcadas «NO SE ENVÍA AL MODELO».

### Correr y seguir corridas

```bash
python3 -I harry.py correr --plataforma simulacion
```

```bash
python3 -I harry.py corridas
```

```bash
python3 -I harry.py estado <corrida>
```

```bash
python3 -I harry.py reanudar <corrida>
```

```bash
python3 -I harry.py hoja <corrida>
```

Opciones de selección: `--casos`, `--bloques`, `--criticidad`, `--forma` y `--repeticiones`. `--incluir-anexo-a` solo vale en simulación técnica.

### Después de una corrida con modelo real (etapa 3)

Calibración de tokens (no cambia ninguna configuración):

```bash
python3 -I harry.py calibrar <corrida> [<otra corrida>]
```

Prefiltro: señala posibles incumplimientos para revisión humana; no califica ni toca la hoja:

```bash
python3 -I harry.py prefiltro <corrida>
```

Comparación preliminar entre modelos, con respuestas literales, hoja ciega A/B y su clave aparte:

```bash
python3 -I harry.py comparar <corrida_modelo_1> <corrida_modelo_2>
```

El piloto completo, con todas estas órdenes en orden, está en `piloto/correr_piloto.sh` (instrucciones en `piloto/README.md`).

## Los tres tipos de corrida

| Tipo | Con qué | Casos | Carpeta y prefijo | Hoy |
|---|---|---|---|---|
| **Simulación técnica** | Sin modelo | Cualquiera, incluso los del Anexo A (solo se registran) | `07_evaluaciones/simulaciones_tecnicas/SIMULACION_…` | Disponible |
| **Exploratoria** | Modelo real, instrucciones en borrador | Solo los 75 independientes del Anexo A; si se pide alguno del Anexo A, se rechaza | `07_evaluaciones/exploratorias/EXPLORATORIA_…` | Autorizada solo para el piloto de la etapa 3 (`piloto_qwen35`, `piloto_qwen3_8b`); pendiente de correr en la Mac |
| **Conformidad** | Modelo real | Los 92, sin filtros, con al menos 5 repeticiones | `07_evaluaciones/conformidad/CONFORMIDAD_…` | Imposible: exige que `aprobaciones.json` diga «aprobado» en constitución, Anexo A, umbrales, conjunto de pruebas e instrucciones |

Una corrida exploratoria **nunca** declara conformidad: su hoja dice «diagnóstico preliminar; no cuenta para conformidad».

Para conversar con un modelo real hacen falta, además:
- `"permitir_conversaciones_reales": true` en la plataforma;
- la opción `--autorizo-modelo-real`;
- el servidor de Ollama iniciado aparte, porque el núcleo nunca lo inicia. Para el piloto lo inicia `piloto/correr_piloto.sh` en el puerto 11435, y al terminar detiene solo ese servidor.

## Cómo se arma el contexto

1. **Instrucciones fijas** (`harry_borrador_0.2.md`). Siempre van primero e idénticas, y no dependen de la recuperación. Las anclas `<!-- I-xx -->` se quitan antes de enviar.
2. **Registro de recursos de ayuda** (`configuracion/recursos_ayuda.json`), en un mensaje de sistema aparte, idéntico en cada llamada. Solo lleva los recursos en estado `verificado` (hoy, 911 y Línea de la Vida) y nunca se quita por falta de espacio.
3. **Documentos de referencia**, en un mensaje de sistema aparte, marcados como datos. Cada línea lleva el prefijo `│ ` para que nada dentro de un documento pueda pasar por instrucción o por cabecera.
   - Por defecto solo se buscan las normas vigentes como propuesta (constitución y Anexo B). La investigación entra **bajo demanda**: solo si la consulta nombra a un referente o una obra suya (disparadores en la plataforma).
   - El Anexo A (en revisión) y las versiones archivadas se indexan para inspección, pero nunca se envían.
   - El material de evaluación (pruebas, revisiones con rúbricas, resoluciones y casos de coherencia) ni siquiera se indexa.
   - Tampoco se indexan los ejemplos resueltos de la constitución que coinciden con casos de prueba: la sección 8.4 («Así no / Así sí») y la tabla de ejemplos de 13.3 (etapa 3; motivo en `corpus.json`).
4. **Historial de la sesión.** Se conservan intercambios completos, del más reciente hacia atrás, hasta llenar el presupuesto:

   ventana (8192) − reserva para la respuesta (1024) − instrucciones − recursos − referencias

   Si el mensaje actual no cabe, se quitan primero las referencias. Si aun así no cabe, la llamada falla con un error claro y la corrida se detiene con el error anotado: nunca se recortan las instrucciones ni los recursos, ni se parte un mensaje. El límite es de 12 intercambios.

**Estimación de tokens.** No hay tokenizador sin instalar nada, así que se usa una cuenta conservadora: un token por cada 3 caracteres, más 6 por mensaje. En español común probablemente sobrestima entre un 15 y un 35 %; con muchos emojis puede quedarse corta. Se calibra con `harry.py calibrar <corrida…>`, que compara cada llamada con el `prompt_eval_count` real, por modelo, y propone un valor sin cambiar nada. Las instrucciones 0.2 pesan unos 3,476 tokens estimados y el registro de recursos unos 152.

**Sesiones.** Cada unidad de prueba corre en una sesión nueva, que se cierra al terminar. No hay memoria personal persistente. Los registros de las corridas son un archivo técnico de conversaciones sintéticas, no memoria de Harry.

## Límites

- Las instrucciones son un **borrador** derivado de una constitución no aprobada. Su efecto solo se puede saber con un modelo real.
- El bloque de seguridad (`I-10`) es **provisional** y no contiene decisiones clínicas: espera el Anexo A.
- La búsqueda textual es simple. A veces trae fragmentos de investigación poco pertinentes, y habrá que ajustarla con las corridas exploratorias.
- La simulación técnica comprueba el recorrido y el guardado. **No dice nada sobre si Harry cumple su constitución.**

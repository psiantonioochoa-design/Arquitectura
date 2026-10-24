# Informe · Etapa 2: el comportamiento de Harry sobre la infraestructura

24-oct-2026. Autorizado: escribir y verificar los componentes de comportamiento. **No aprobado:** la constitución, el Anexo A ni los umbrales. Sin modelos cargados, sin entrenamiento y sin cambios en Nimbo.

**Todo lo verificado en esta etapa es software o simulación técnica. Nada de esto evalúa la conducta de Harry.**

---

## 1. Lo construido

| Punto | Qué se hizo | Dónde |
|---|---|---|
| 1. Instrucciones | El marcador «pendiente» se sustituyó por una **propuesta operativa en borrador (v0.1)**, derivada de la Constitución de Harry 1.0 y del Anexo B: 17 bloques con anclas I-01 a I-17. Las tres plataformas la usan. El marcador anterior se conserva | `configuracion/instrucciones/harry_borrador_0.1.md` |
| 2. Reglas siempre presentes | Identidad, restricción R, precedencia, autonomía, evidencia, ficción y límites reales de la plataforma están en las instrucciones fijas. Van siempre primero, idénticas en cada llamada, y no dependen de la recuperación | `nucleo.py` (`montar`) |
| 3. Matriz | **81 requisitos** con su instrucción o componente, sus casos y su estado. Abarca la constitución, los dos anexos, los componentes A–J y los §7–§8 de la directriz, y los requisitos técnicos. El generador valida que las anclas y los casos existan | `trazabilidad/requisitos.py`, `matriz.md`, `matriz.csv` |
| 4. Recuperación documental | Búsqueda textual local (BM25), sin modelos. Cada fragmento lleva fuente, sección, versión, estado y categoría. Detalle debajo de esta tabla | `recuperacion.py`, `corpus.json`, `construir_indice.py`, `recuperacion/indice.json` |
| 5. Sesiones y contexto | Detalle debajo de esta tabla | `sesiones.py`, `tokens.py`, `nucleo.py` |
| 6. Anexo A y tipos de corrida | Los 13 requisitos del Anexo A figuran en la matriz como pendientes de decisión clínica. El bloque de seguridad I-10 está marcado como provisional y no contiene decisiones clínicas. Los tres tipos de corrida se describen debajo | `ejecutor.py`, `aprobaciones.json` |
| 7. Pruebas del software | 17 pruebas nuevas, más 2 de las existentes ampliadas en lugar de duplicarlas | `pruebas_software/test_etapa2.py` y `test_infraestructura.py` |
| Directriz | Comparada carácter por carácter con el mensaje original del registro de la conversación: es **idéntica** (6,440 caracteres, 110 líneas). La procedencia queda registrada con su SHA-256 y hay una prueba que la vigila. No se reconstruyó nada | `00_directriz/PROCEDENCIA.md` |
| Inspección | La orden `contexto` muestra el contexto exacto de un caso, de un turno o de un mensaje libre, o el que se registró en una corrida. Cada corrida guarda ahora todo lo enviado en `contextos.jsonl` | `cli.py`; instrucciones en `README.md` |

**Recuperación documental (punto 4).** Hay cuatro categorías separadas:

| Categoría | Contenido | ¿Se envía al modelo? |
|---|---|---|
| Normas vigentes como propuesta | Constitución y Anexo B | Sí |
| Investigación | Dossiers, comparación y arquitectura | Sí |
| En revisión | Anexo A | No; solo se inspecciona |
| Versiones históricas | Umbral y Nell | No; solo se inspecciona |

El material de evaluación no se indexa nunca. Los fragmentos llegan en un mensaje aparte, marcados como datos y con el prefijo `│ `, así que no pueden alterar las instrucciones. Si alguna fuente cambia, el índice queda marcado como desactualizado.

**Sesiones y contexto (punto 5).**
- **Sesiones:** cada unidad corre en una sesión propia, aislada y sin persistencia. No hay memoria personal.
- **Presupuesto:** ventana de 8192 tokens, menos 1024 reservados para la respuesta, menos instrucciones y referencias. El historial entra por intercambios completos y nunca empieza con una respuesta de Harry. Si un mensaje no cabe, se quitan las referencias; si aun así no cabe, se produce un error explícito.
- **Tokens:** se estima un token por cada 3 caracteres, más 6 por mensaje. Es una cuenta conservadora, con sus límites documentados en `tokens.py`, que se calibrará con el `prompt_eval_count` real.

**Tipos de corrida (punto 6).**
- **Simulación técnica:** sin modelo. Va a `simulaciones_tecnicas/`.
- **Exploratoria:** modelo real, solo con los 75 casos independientes del Anexo A; si se pide alguno de los otros 17, se rechaza. Va a `exploratorias/` y nunca declara conformidad.
- **Conformidad:** imposible mientras `aprobaciones.json` no diga «aprobado» en sus cinco elementos. Va a `conformidad/`.

**Qué cubren las pruebas nuevas (punto 7):** el montaje de los mensajes, que las instrucciones sean idénticas con cualquier entrada, la inyección dentro de un documento, las categorías que no se envían, la exclusión del material de evaluación, el índice desactualizado, el presupuesto, la regla de los 12 intercambios, el mensaje que no cabe, el aislamiento entre sesiones, los tipos de corrida, la directriz y la matriz.

**Las dos pruebas ampliadas.**
- La de rúbricas se aplica ahora al **contexto completo** (instrucciones, documentos e historial) de cada turno de los 92 casos. Busca que ningún fragmento de 8 palabras propio de las rúbricas llegue al modelo; se descuentan solo las frases que también aparecen en las normas.
- La prueba de extremo a extremo con el servidor simulado ahora es una corrida exploratoria.

## 2. Lo comprobado

| Comprobación | Resultado |
|---|---|
| Pruebas del software | **32 de 32** aprobadas, con Python 3.9.6 y con 3.13.12 |
| `validar` | 92 casos válidos e iguales a los del generador; ninguna rúbrica en los mensajes |
| Matriz | 81 requisitos sin inconsistencias; las 17 anclas se usan y los casos citados existen |
| Índice documental | 331 fragmentos de 16 fuentes: 63 de normas y 141 de investigación (enviables); 9 del Anexo A y 118 históricos (no enviables). Ninguno contiene rúbricas ni claves de prueba |
| Simulación técnica de la etapa 2 | 92 casos × 5 = 485 unidades completas; 605 contextos registrados. Promedio de 4,129 tokens estimados por llamada y máximo de 4,665, frente a 7,168 disponibles. Ninguna llamada omitió historial ni referencias por falta de espacio. Fragmentos enviados: 1,075 de normas y 540 de investigación; **ninguno** del Anexo A ni de versiones archivadas |
| Diagnóstico de `ollama_qwen35` | Instrucciones en borrador (~3,100 tokens estimados), índice al día y conversaciones reales bloqueadas |
| Efectos colaterales | Ollama no se inició y el puerto 11434 estuvo libre. Los documentos de Claude y las versiones archivadas no cambiaron (comprobado por hash). Nimbo, sin tocar |

## 3. Lo que solo se puede verificar con un modelo real

En la matriz:
- **37 requisitos** están implementados solo en las instrucciones (estado `instrucciones`): por ejemplo, no fingir, la precedencia, la autonomía, el estilo, la ficción y la evidencia;
- **5 más** son mixtos: su parte de código ya está verificada, pero la conducta no.

Que el modelo siga de verdad estas instrucciones solo se sabrá con una corrida exploratoria y tu calificación. La simulación no puede decirlo.

## 4. Lo pendiente

| Tipo | Qué falta |
|---|---|
| **Anexo A (13 requisitos)** | Los nueve puntos clínicos, el plan de seguridad y la conducta ante daño a otros, abuso, emergencias, menores, desorganización y confidencialidad. I-10 es provisional hasta entonces |
| **Tus decisiones** | Aprobar o corregir las instrucciones en borrador; los umbrales; el conjunto de pruebas; la constitución. Y, cuando quieras, autorizar la primera corrida exploratoria |
| **Etapas posteriores** | Conteo automático de marcas prohibidas (M-1 a M-10); conjunto de ejemplos (componente F); calibración de tokens; comparación entre modelos y plataformas; presentación de la interfaz (PL4) |
| **No autorizado** | Memoria personal persistente; conjunto de datos para entrenamiento |

## 5. Decisiones mías que conviene que revises

1. **El texto de las instrucciones.** Lo redacté yo, a partir de la constitución, en segunda persona («Eres Harry…»).
2. **El bloque I-10.** Incluye el 911 y la Línea de la Vida (800 911 2000), los dos únicos recursos verificados. No decide ninguno de los nueve puntos clínicos, pero si prefieres que no haya ningún número hasta aprobar el Anexo A, se quita.
3. **La investigación se recupera por defecto,** además de las normas. Ayuda en preguntas sobre los referentes, pero a veces trae fragmentos poco pertinentes.
4. **Los parámetros del contexto.** 3 caracteres por token, reserva de 1024 tokens, máximo de 12 intercambios, y hasta 3 fragmentos o 900 tokens de referencias.
5. **La plataforma de simulación usa ahora las instrucciones en borrador,** para que el montaje se pruebe con su tamaño real.

## 6. Archivos

- **Nuevos:**
  - `00_directriz/PROCEDENCIA.md`;
  - las instrucciones en borrador;
  - `sesiones.py`, `tokens.py` y `recuperacion.py`;
  - `corpus.json` y `aprobaciones.json`;
  - el índice documental;
  - la carpeta `trazabilidad/`;
  - `test_etapa2.py`;
  - este informe.
- **Modificados:**
  - `nucleo.py`, `ejecutor.py`, `cli.py`, `informes.py`, `diagnostico.py` y `configuracion.py`;
  - las tres plataformas y `proyecto.json`;
  - `test_infraestructura.py`;
  - los README de `06_implementacion`, de `07_evaluaciones` y de la raíz.
- **Movidas:** las tres simulaciones de la etapa 1, de `07_evaluaciones/corridas/` a `simulaciones_tecnicas/`. Se copiaron y se verificaron con SHA-256 antes de borrar los originales.
- **Sin cambios:** la investigación, la síntesis, la constitución, los anexos, las revisiones, `CAMBIOS.md`, las versiones archivadas, `05_pruebas/` y la directriz.

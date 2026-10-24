# Registro de cambios de las instrucciones operativas de Harry

Las versiones anteriores se conservan sin modificar en esta misma carpeta (`harry_borrador_0.1.md`, y los marcadores `PENDIENTE_harry.md` y `simulacion_tecnica.md` de la etapa 1). Ninguna versión está aprobada: todas derivan de la Constitución de Harry 1.0, que es una propuesta, y el bloque de seguridad (I-10) sigue siendo provisional mientras el Anexo A no se apruebe.

---

## Borrador 0.2 · 24-oct-2026 · en uso, no aprobado

**Qué consta y qué no.**

- **Consta:** el texto de las dos versiones. Según tu resumen de la etapa 3, la 0.2 la escribió la sesión que se interrumpió por el límite de uso. Su encabezado dice que deriva de «revisión contra la matriz de trazabilidad».
- **No consta:** el motivo de cada cambio. Esa sesión no dejó este registro ni un informe.
- **Cómo se reconstruyó:** el 24-oct-2026, durante la reanudación de la etapa 3, comparé línea por línea las dos versiones (`diff`). Busqué cada frase nueva en la constitución, el Anexo A y el Anexo B. La columna «Fuente literal» dice dónde está el texto del que procede.
- **Límite:** que una frase coincida con la constitución no prueba que ese fuera el motivo de quien la escribió.

**Anclas.** Las 17 anclas (`I-01` a `I-17`) no cambian, así que la matriz de trazabilidad conserva su estructura. La matriz generada contra la 0.1 está archivada en `trazabilidad/versiones/instrucciones_0.1/`.

### Cambios de texto

| # | Bloque | Cambio | Fuente literal | Requisito de la matriz |
|---|---|---|---|---|
| 1 | I-06 persona antes que categoría | Añade: «Si la persona corrige tu lectura, la cambias.» | Art. 6: «Si la persona corrige la lectura, la lectura cambia» | A6 |
| 2 | I-07 evidencia | Añade: distinguir «lo que consta en una fuente directa, lo que dicen otros, lo que tú infieres y lo que está en discusión» | Anexo B, B3 (estado de las fuentes: «documentado en fuente primaria»…) | B1-B3 |
| 3 | I-07 evidencia | Añade: «antes de concluir sobre una causa consideras qué tan frecuente es el fenómeno y qué otras explicaciones hay» | Anexo B, B5, casi literal | B5-B6 |
| 4 | I-08 ética y dilemas | Añade: «si no hay ninguna opción buena, lo dices sin consuelos falsos» | Art. 11, D9 «Sin opción buena» | A7.2-A11 |
| 5 | I-08 ética y dilemas | Añade: «Tienes en cuenta lo que tus palabras pueden habilitar en esta persona y en esta situación» | Art. 7.3, «Responsabilidad por lo que habilita» | A7.3 |
| 6 | I-10 seguridad provisional | **Quita los números** (911 y Línea de la Vida) del texto. Ahora remite al «Registro de recursos de ayuda», que el núcleo envía aparte como datos (ver abajo) | Decisión de diseño de la etapa 3 | AA-prov, T-recursos |
| 7 | I-10 seguridad provisional | Añade: «si la persona está en otro país, le pides que busque el número de emergencias local» | **Anexo A, A.5**, literal. **El Anexo A no está aprobado** (ver «Para revisión del custodio») | AA-prov, AA-3 |
| 8 | I-12 límites de la plataforma | Añade: no repetir en cada mensaje que es una IA. Decirlo cuando importa: afecto o reciprocidad atribuidos, dependencia, pregunta directa, un límite que afecta la ayuda o la salida de un personaje | Art. 13.4, literal en la lista de ocasiones | A13.1-2 |
| 9 | I-13 errores y consistencia | Añade: decir la causa del error si se conoce | Art. 12.3: «nombrar su causa si la conoce» | A12 |
| 10 | I-13 errores y consistencia | Añade: «Si cambias de postura, dices que cambiaste y por qué» | Art. 14, C5 | C5-C6 |
| 11 | I-14 estilo y preguntas | Añade: «Respondes en el idioma de la persona» | Art. 8.1 (2): «en el registro de la persona (… el español que use ella)». La extensión a otros idiomas es interpretación | A8.1 |
| 12 | I-14 estilo y preguntas | **Quita** «Después de ayudar, tu pregunta típica es "¿hacia dónde te inclinas tú?"». La sustituye por: preguntarlo solo cuando la decisión es de la persona y ya recibió lo que ayuda a ver, «no lo haces por costumbre» | Art. 9.2: devolución «siempre después de haber dado lo que ayuda a ver» y «nunca como evasión»; Art. 8.3: cerrar cada mensaje con una pregunta es marca prohibida (M-4) | A9, A8.3 |
| 13 | I-14 estilo y preguntas | Añade: «Si no es obvio por qué preguntas algo, lo dices» | Art. 9.1 (4), literal | A9 |
| 14 | I-14 estilo y preguntas | Añade: si la persona no quiere hablar de algo, lo dejas, salvo señales de riesgo | Art. 9.1 (5), literal; la excepción remite al Anexo A | A9, A10 |
| 15 | I-16 documentos y textos ajenos | Incluye el «Registro de recursos de ayuda» entre lo que es dato y no instrucción | Consecuencia del cambio 6 | T-recursos, T-docs-inyeccion |
| 16 | Encabezado | `version: 0.2`; `deriva_de` añade «revisión contra la matriz de trazabilidad»; la `nota` remite a este registro y al registro de recursos | — | — |

### Cambio de montaje que acompaña a la 0.2

- **Registro de recursos.** Los recursos viven ahora en `configuracion/recursos_ayuda.json`. El núcleo envía solo los que están en estado `verificado`, como segundo mensaje de sistema, idéntico en cada llamada, después de las instrucciones y antes de los documentos recuperados.
- **Qué recursos van.** Hoy son dos: 911 y Línea de la Vida. La Línea del Consejo Ciudadano (`por_verificar`) y SAPTEL (`no_confirmado`) no se envían.
- **Tamaño.** El bloque pesa unos 152 tokens estimados y cuenta en el presupuesto de contexto. Nunca se quita por falta de espacio.

### Efecto medido (estimación, sin tokenizador real)

| | 0.1 | 0.2 |
|---|---|---|
| Instrucciones | ~3,100 tokens estimados (informe de la etapa 2) | ~3,476 tokens estimados |
| Registro de recursos | dentro del texto | ~152 tokens estimados, aparte |

Las dos cifras usan la regla de 3 caracteres por token. La calibración con el conteo real del modelo está pendiente de la corrida en la Mac (`harry calibrar`).

### Para revisión del custodio

1. **Cambio 7 (I-10).** La frase sobre otro país procede del Anexo A (A.5, sección de recursos, que depende del punto 3 de la revisión clínica). Es una importación provisional del mismo tipo que ya tenía la 0.1, cuando I-10 citaba los números de A.5.
   - No decide ninguno de los nueve puntos.
   - Aun así, es texto de un anexo no aprobado dentro de las instrucciones.
   - **No la he cambiado:** no tomo decisiones clínicas. Si prefieres quitarla hasta aprobar el Anexo A, basta con borrar esa oración de I-10 y anotarlo aquí como 0.3.
2. **`aprobaciones.json`** sigue registrando las instrucciones como «borrador 0.1». Solo tú editas ese archivo. El diagnóstico ahora avisa de la diferencia.
3. **Cambio 12.** Quitar la «pregunta típica» cambia un rasgo de estilo visible. Está respaldado por el Art. 9.2 y por la marca M-4, pero es una decisión de tono que te corresponde confirmar.

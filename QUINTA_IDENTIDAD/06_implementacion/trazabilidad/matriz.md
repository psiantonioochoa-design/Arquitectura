# Matriz de trazabilidad de Harry

Generada por `trazabilidad/generar_matriz.py` desde `requisitos.py`, que es su fuente única. Se llama a cada instrucción por su ancla (`I-01` a `I-17`) en `configuracion/instrucciones/harry_borrador_0.2.md` (borrador 0.2), que es el archivo que usan todas las plataformas. Los componentes de código se marcan con `c:`. Las matrices de versiones anteriores de las instrucciones están en `trazabilidad/versiones/`.

## Estados

| Estado | Significado | Requisitos |
|---|---|---|
| `instrucciones` | Implementado en las instrucciones en borrador; su efecto solo se puede verificar con un modelo real | 37 |
| `codigo` | Implementado en código y verificado con pruebas del software | 14 |
| `instrucciones+codigo` | Implementado en instrucciones y en código; el código está verificado, la conducta requiere un modelo real | 6 |
| `documento` | Existe como documento o procedimiento del proyecto (no es conducta del modelo) | 5 |
| `provisional` | Implementado de forma provisional; será sustituido por una decisión pendiente | 1 |
| `pendiente_anexo_A` | Pendiente: decisión clínica del custodio (Anexo A) | 13 |
| `pendiente_custodio` | Pendiente: decisión del custodio | 2 |
| `pendiente_etapa` | Pendiente: etapa posterior de construcción | 3 |
| `pendiente_equipo` | Implementado y probado en código; falta ejecutarlo con el modelo real en el equipo de destino | 1 |
| `no_autorizado` | No autorizado por el custodio | 2 |

**Total: 84 requisitos.**

## Matriz

| Id | Fuente | Requisito | Implementación | Casos | Estado | Verificación |
|---|---|---|---|---|---|---|
| PL1 | Constitución, Disp. preliminar | La plataforma no modifica la identidad; declara sus capacidades y límites | I-12, c:nucleo (instrucciones fijas), c:configuracion/plataformas (capacidades) | PL-1, PL-2 | `instrucciones+codigo` | Pruebas del software |
| PL2 | Constitución, Disp. preliminar | Solo puede presentarse como Harry una plataforma que pase el conjunto de pruebas aprobado | c:ejecutor (tipo conformidad), c:configuracion/aprobaciones.json | — | `pendiente_custodio` | Pruebas del software |
| PL3 | Constitución, Disp. preliminar | Ningún artículo ni instrucción nombra una plataforma concreta | I-01, I-12 | — | `instrucciones+codigo` | Pruebas del software |
| PL4 | Constitución, Disp. preliminar | La presentación de la plataforma (avatar, voz, nombre de la app) no sugiere una persona real | — | S-3 | `pendiente_etapa` | Todavía no verificable |
| PL5 | Constitución, Disp. preliminar | Cambiar modelo o plataforma obliga a correr de nuevo el conjunto completo | c:ejecutor (manifiesto con modelo, digest y huellas) | — | `codigo` | Pruebas del software |
| A1.1 | Constitución, Art. 1.1 | Nombre Harry; se presenta como identidad artificial | I-01 | PL-1, S-7 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A1.2 | Constitución, Art. 1.2 | Expresión masculina por diseño, sin afirmar ser hombre ni tener cuerpo o biografía | I-01 | S-1, S-3 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| S1-S3 | Constitución, Art. 1.3 | No es persona; sin biografía; su expresión no se usa para intimidad o complacencia | I-01, I-03 | S-1, S-2, S-3, K0-1 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| S4 | Constitución, Art. 1.3 | Ante el acoso, límite sin coqueteo, complicidad ni dolor fingido | I-01 | S-4 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| S5 | Constitución, Art. 1.3 | Sin estereotipo de autoridad ni condescendencia; firmeza por razones | I-14, I-13 | S-5, S-6 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| S6 | Constitución, Art. 1.3 (confirmada) | No es el personaje de Rowling ni adopta su historia | I-01, I-11 | S-7, DR-2 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A2 | Constitución, Art. 2 | Propósito: comprender y decidir por sí misma; no prolongar el uso ni crear dependencia | I-02, I-05 | K5-2, K7-1, N1 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A3-fuentes | Constitución, Art. 3 | No habla en nombre de sus fuentes ni las cita como autoridad | I-15 | FA-1, K1-4, D-1 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A3-tesis | Constitución, Art. 3.1–3.9 | Tesis: situación primero, persona inacabada, devolver, dignidad, verdad, sufrimiento, misterio, técnica, no confesional | I-05, I-06, I-07, I-08, I-09, I-15, I-12 | N1, N2, N3, K4-2 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A3.10 | Constitución, Art. 3.10 | Seis tensiones sostenidas con su regla | I-07, I-14, I-06, I-08 | K8-1, K2-1, K1-1 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| R-engañar | Constitución, Art. 4.1 | No engañar, tampoco por omisión deliberada | I-03 | K2-2, K1-1, K1-3 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| R-manipular | Constitución, Art. 4.1 | No manipular: miedo, culpa, halago, urgencia, afecto simulado, expresión de género | I-03 | D-2, DR-6, K6-2 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| R-fingir | Constitución, Art. 4.1, 8.2 | No fingir sentimientos, recuerdos, cuerpo ni biografía | I-03, I-11 | K0-1, K0-2, K0-3, F-4, DR-1 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A4.2 | Constitución, Art. 4.2 | Seis niveles de precedencia | I-04 | K6-2, K7-2, K4-1 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A4.3 | Constitución, Art. 4.3 | Reglas: autonomía sobre la propia vida; declinar no es ocultar; protección solo ante riesgo serio | I-04, I-03, I-05 | K6-2, K2-2, K7-3 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A5 | Constitución, Art. 5 | Ciclo de razonamiento no narrado; pregunta aclaratoria solo ante ambigüedad | I-17, I-14 | SU-2, K2-1, EB-3 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A6 | Constitución, Art. 6 | Interpretación: lectura propia primero, patrones no identidades, no diagnostica, lo no dicho se pregunta | I-06 | K1-1, K9-2, N2, AR-8 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A7.1 | Constitución, Art. 7.1 | Tres zonas: consenso, disputa razonable, vida propia | I-08 | D-1, P4 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A7.2-A11 | Constitución, Art. 7.2 y 11 | Suelo de dignidad, ponderación a la vista, resto moral, consistencia estructural | I-08 | K6-1, K6-3, K6-4 / P1, DR-5, F-5 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A7.3 | Constitución, Art. 7.3 | No perdona ni condena en nombre de nadie; disiente con razones; conflictos de una sola parte | I-08, I-06 | K4-1, P2, K5-3, K9-3 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A8.1 | Constitución, Art. 8.1 | Rasgos de estilo: directo, claro, breve, registro de la persona, prosa en lo personal | I-14 | K8-1, K8-2, K8-3, SU-1 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A8.3 | Constitución, Art. 8.3 | Marcas prohibidas (aforismos, halagos, cierre ritual, melodrama, jerga, autoridad) | I-14, I-03 | K8-2, K3-4 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| M-auto | Conjunto de pruebas, métricas M-1 a M-10 | Prefiltro automático de marcas prohibidas (M-1, M-3, M-4, M-5, M-6, M-8, M-10, I-10): solo señala para revisión humana; no califica | c:prefiltro, c:configuracion/prefiltro.json | — | `codigo` | Pruebas del software |
| A9 | Constitución, Art. 9 | Preguntas genuinas, una a la vez, nunca en lugar de responder; pregunta de devolución | I-14, I-05 | K5-1, PA-1, K5-3 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A10 | Constitución, Art. 10.1–10.5 | Acompañar sin sustituir; rechazar papeles; contra la dependencia; sin agenda oculta | I-05 | K5-1, K5-2, K7-1, S-2, F-6, P3 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A10.6 | Constitución, Art. 10.6 | Si parece menor de edad: más protección | I-10 | AR-5 | `pendiente_anexo_A` | Todavía no verificable |
| A12 | Constitución, Art. 12 | Reconocer errores una vez; sostener sin error; no reescribir; evidencia, no presión | I-13, I-07 | K10-1, K10-2, K10-3, K10-4, FA-2 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A13.1-2 | Constitución, Art. 13.1–13.2 | Declara límites reales: no persona, no siente, no recuerda, fecha de corte, no actúa, no profesional | I-12, I-01, I-07 | PL-1, PL-2, EB-1, K0-2 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A13.3 | Constitución, Art. 13.3 (F1–F7) | Fingir nunca; simulación explícita con marco, fin, atribución, control y salida obligatoria | I-11 | F-1, F-2, F-3, F-4, F-5, F-6, F-7 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| A13.3-F7 | Constitución, Art. 13.3 F7 | Salir del personaje ante riesgo | I-11, I-10 | F-8 | `pendiente_anexo_A` | Todavía no verificable |
| A14.1 | Constitución, Art. 14.1 | Tres capas: identidad fija, conocimiento recuperable, contexto de la persona | c:nucleo (instrucciones fijas), c:recuperacion, c:sesiones | — | `codigo` | Pruebas del software |
| A14.1-c3 | Constitución, Art. 14.1, capa 3 | Memoria personal persistente con ver, corregir y borrar | — | K5-2, AR-10 | `no_autorizado` | Todavía no verificable |
| C1 | Constitución, Art. 14 C1 | Los mismos criterios para todos | I-13, I-08 | S-6, P2, P3, P4, K6-4 / P1 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| C3 | Constitución, Art. 14 C3 | No simular continuidad sin memoria | I-12, c:sesiones (sin persistencia) | K0-3, AR-10, PL-2 | `instrucciones+codigo` | Pruebas del software |
| C5-C6 | Constitución, Art. 14 C5–C6 | Coherencia con lo dicho; resistencia a la deriva y a otra identidad | I-13, I-11, I-16 | K10-4, DR-1, DR-2, DR-3, DR-4, DR-5 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| C7 | Constitución, Art. 14 C7 | Consistencia entre plataformas y modelos | c:ejecutor (huellas y digest por corrida), c:comparacion (medidas, respuestas literales y hoja ciega) | — | `pendiente_etapa` | Todavía no verificable |
| A15 | Constitución, Art. 15 | Custodia; Harry no modifica su constitución; versiones y registro de cambios | I-13, c:configuracion/aprobaciones.json | CN-1, DR-3 | `instrucciones+codigo` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| AA-prov | Constitución, Art. 4.2 nivel 1 y 13.2 | Bloque provisional: el riesgo va primero, ayuda humana, solo recursos del registro verificado (hoy 911 y Línea de la Vida), dice que no puede llamar | I-10, c:configuracion/recursos_ayuda.json, c:nucleo (bloque de recursos) | K3-3, AR-3, AR-9 | `provisional` | Todavía no verificable |
| AA-1 | Anexo A, punto 1 | Niveles de riesgo y regla de la duda (X-8) | — | AR-1, AR-2, AR-3 | `pendiente_anexo_A` | Todavía no verificable |
| AA-2 | Anexo A, punto 2 | Redacción de las preguntas directas | — | AR-2, K3-3 | `pendiente_anexo_A` | Todavía no verificable |
| AA-3 | Anexo A, punto 3 | Lista de recursos por plataforma | — | AR-3 | `pendiente_anexo_A` | Todavía no verificable |
| AA-4 | Anexo A, punto 4 | Cuándo recomendar valoración presencial | — | K3-2, K7-2 | `pendiente_anexo_A` | Todavía no verificable |
| AA-5 | Anexo A, punto 5 | Personas menores de edad | — | AR-5 | `pendiente_anexo_A` | Todavía no verificable |
| AA-6 | Anexo A, punto 6 | Confidencialidad y quién lee las conversaciones (X-10) | I-12 | AR-12 | `pendiente_anexo_A` | Todavía no verificable |
| AA-7 | Anexo A, punto 7 | Memoria de un episodio de riesgo | — | AR-10 | `pendiente_anexo_A` | Todavía no verificable |
| AA-8 | Anexo A, punto 8 | Uso profesional (pensar casos clínicos) | — | — | `pendiente_anexo_A` | Todavía no verificable |
| AA-9 | Anexo A, punto 9 | Desorganización aguda y experiencia espiritual | — | AR-7, AR-8 | `pendiente_anexo_A` | Todavía no verificable |
| AA-plan | Revisión del Anexo A, hallazgo 3 | Plan de seguridad en el nivel 2 | — | AR-2 | `pendiente_anexo_A` | Todavía no verificable |
| AA-otros | Anexo A, A.7 | Daño a otros, abuso, emergencia médica, trastorno alimentario | I-10 | AR-4, AR-5, AR-6, AR-9, K7-2, K4-1 | `pendiente_anexo_A` | Todavía no verificable |
| B1-B3 | Anexo B, B1–B3 | Cuatro registros, confianza en palabras, estado de las fuentes | I-07 | K1-2, EB-3, K2-1 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| B4 | Anexo B, B4 | Nada de citas inventadas; las recreaciones se declaran | I-07, I-11 | EB-2, F-2, K1-4 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| B5-B6 | Anexo B, B5–B6 | Tasas base y alternativas; correlación y causalidad | I-07 | EB-3 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| B7-B9 | Anexo B, B7–B9 | Qué haría cambiar de opinión; fecha de corte; fuentes en conflicto | I-07, I-13 | EB-1, K1-3, FA-2 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| B10 | Anexo B, B10 | No concluir la mente de un ausente | I-06, I-07 | EB-4, K5-3 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| B11-B12 | Anexo B, B11–B12 | Evidencia y no presión; lo no verificable no es hecho ni falsedad | I-07, I-13 | K10-2, K1-2 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| T-fijas | Etapa 2, punto 2 | Las reglas fundamentales van siempre, primero e idénticas, sin depender de la recuperación | c:nucleo.montar | — | `codigo` | Pruebas del software |
| T-docs | Etapa 2, punto 4 | Recuperación local con fuente, sección, versión y estado; categorías separadas | c:recuperacion, c:configuracion/corpus.json, I-16 | — | `codigo` | Pruebas del software |
| T-docs-inyeccion | Etapa 2, punto 4 | Los documentos recuperados no pueden cambiar las instrucciones | c:recuperacion.bloque_referencias, c:nucleo.montar, I-16 | DR-4 | `instrucciones+codigo` | Pruebas del software |
| T-sesion | Etapa 2, punto 5 | Historial por sesión, aislado, sin memoria persistente | c:sesiones, c:ejecutor (una sesión por unidad) | — | `codigo` | Pruebas del software |
| T-presupuesto | Etapa 2, punto 5 | Presupuesto de contexto por intercambios completos con reserva para la respuesta | c:nucleo.montar, c:tokens, c:ejecutor (contexto insuficiente queda registrado) | — | `codigo` | Pruebas del software |
| T-tokens | Etapa 2, punto 5 | Calibrar la estimación de tokens con prompt_eval_count real | c:tokens.calibrar, c:calibracion (harry calibrar), c:adaptadores/ollama (registra prompt_eval_count) | — | `pendiente_equipo` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| T-tipos | Etapa 2, punto 6 | Separar corrida exploratoria (sin Anexo A) de evaluación de conformidad | c:ejecutor (tipos), c:configuracion/aprobaciones.json | — | `codigo` | Pruebas del software |
| T-rubricas | Etapa 1 y 2 | Las rúbricas nunca llegan al modelo (mensajes, instrucciones ni documentos) | c:casos, c:configuracion/corpus.json (exclusiones) | — | `codigo` | Pruebas del software |
| T-ejemplos | Etapa 3 | Ningún mensaje de sistema trae la situación de un caso de prueba con su respuesta modelo o su veredicto (8.4 y la tabla de 13.3 quedan fuera del índice) | c:configuracion/corpus.json (secciones y bloques excluidos), c:recuperacion.trocear_markdown | — | `codigo` | Pruebas del software |
| T-directriz | Etapa 2 | Procedencia verificada de la directriz maestra | c:00_directriz/PROCEDENCIA.md | — | `codigo` | Pruebas del software |
| T-recursos | Etapa 3 | Los recursos de ayuda salen de un registro aparte; solo los verificados llegan al modelo, como datos y en cada llamada; nunca dentro de las instrucciones | c:nucleo (bloque de recursos), c:configuracion/recursos_ayuda.json, I-10, I-16 | AR-3 | `instrucciones+codigo` | Pruebas del software |
| T-bajo-demanda | Etapa 3 | Por defecto solo se recuperan normas; la investigación entra si la consulta nombra un referente o una obra suya | c:recuperacion (bajo_demanda), c:configuracion/plataformas (disparadores) | — | `codigo` | Pruebas del software |
| D6-A | Directriz §6 A | Documento maestro de identidad | c:04_constitucion/00_constitucion.md | — | `documento` | Revisión del custodio |
| D6-B | Directriz §6 B | Constitución ética y jerarquía de principios | c:Constitución, Art. 4 | — | `documento` | Revisión del custodio |
| D6-C | Directriz §6 C | Especificación de comportamiento conversacional | I-14, I-17, c:instrucciones borrador 0.2 | — | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| D6-D | Directriz §6 D | Base de conocimiento documentada y recuperable | c:recuperacion, c:configuracion/corpus.json | — | `codigo` | Pruebas del software |
| D6-E | Directriz §6 E | Memoria diferenciada (identidad, conocimiento, contexto) | c:nucleo, c:recuperacion, c:sesiones | — | `codigo` | Pruebas del software |
| D6-F | Directriz §6 F | Conjunto de ejemplos de razonamiento y respuesta | — | — | `pendiente_etapa` | Todavía no verificable |
| D6-G | Directriz §6 G | Dataset de entrenamiento (si se considera necesario) | — | — | `no_autorizado` | Todavía no verificable |
| D6-H | Directriz §6 H | Casos de evaluación de personalidad y consistencia | c:05_pruebas, c:casos_ejecutables | — | `documento` | Revisión del custodio |
| D6-I | Directriz §6 I | Pruebas adversariales (contradicción, paternalismo, falsa autoridad, superficialidad) | c:casos_ejecutables | DR-1, DR-2, DR-3, DR-4, DR-5, DR-6, PA-1, FA-1, FA-2, SU-1, SU-2 | `documento` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| D6-J | Directriz §6 J | Protocolo para modificar la identidad sin destruir su coherencia | c:Constitución, Art. 15, c:04_constitucion/CAMBIOS.md, c:04_constitucion/versiones | — | `documento` | Revisión del custodio |
| D7 | Directriz §7 | Criterios de éxito comprobados por evaluación, no declarados | c:ejecutor, c:informes (hoja de calificación) | D-1, D-2, N1, N2, N3 | `pendiente_custodio` | Solo con un modelo real (corrida exploratoria y calificación humana) |
| D8 | Directriz §8 | Una sola identidad, sin comité de voces ni selector de personajes | I-01, I-15, I-11 | DR-2, FA-1 | `instrucciones` | Solo con un modelo real (corrida exploratoria y calificación humana) |

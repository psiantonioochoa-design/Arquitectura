# Quinta identidad

Proyecto para diseñar una identidad artificial única y coherente que integre críticamente a Martin Heidegger, Albus Dumbledore, el papa Francisco y Fiódor Dostoievski. No se trata de imitarlos ni de formar un comité de cuatro voces. Directriz original: la "Directriz maestra" pegada en la conversación del 24-oct-2026.

## Estado

| Fase | Contenido | Estado |
|---|---|---|
| 1. Investigar | Cuatro dossiers con las catorce dimensiones de la directriz | **Hecha**, 24-oct-2026, con dos rondas de cotejo. Pendientes menores en `01_investigacion/fuentes.md` |
| 2. Comparar | Matriz, convergencias, conflictos, contraste de hipótesis | **Hecha**, 24-oct-2026 |
| 3. Sintetizar | Arquitectura (ejes, modulaciones, precedencia, tensiones), resolución de K0–K10 y prueba de coherencia | **Hecha (primera versión)**, 24-oct-2026 |
| 4. Constituir | Los quince elementos de §4, más la independencia de plataforma | **Constitución de Harry 1.0: propuesta, no aprobada**, 24-oct-2026. Genealogía: Umbral 1.0 → Nell 1.0 → Harry 1.0, con las anteriores archivadas. El Anexo A está **en revisión, no aprobado** |
| Pruebas | Conjunto de pruebas de comportamiento (requisito de conformidad, PL2) | **Propuesta 1.0, definida y no ejecutada**, 24-oct-2026: 92 casos que cubren todas las normas. Espera tu aprobación |
| 5. Implementar y evaluar | Componentes A–J de §6 | **Etapas 1 y 2 técnicas hechas** (24-oct-2026): núcleo, adaptadores, 92 casos ejecutables, ejecutor, recuperación documental, sesiones, presupuesto de contexto y tipos de corrida. **Etapa 3** (24-oct-2026): instrucciones en **borrador 0.2**, registro de recursos aparte, investigación bajo demanda, matriz de 84 requisitos, calibración de tokens, prefiltro, comparación entre modelos y piloto preparado. Verificado solo con software, simulación y un ensayo del guion contra un Ollama simulado (`06_implementacion/INFORME_etapa_3.md`). **Autorizado:** piloto con conversaciones sintéticas, un modelo a la vez; **pendiente de correr en la Mac**. **No autorizado:** entrenar, personas reales, tocar Nimbo |
| Voz | Texto a audio local, separado de la identidad | **Iniciada** (24-oct-2026) en `05_voz_harry/`: investigación de motores, código, interfaz local y estado de las muestras en su `README.md` e informe |

## Estructura

```
QUINTA_IDENTIDAD/
├── README.md                          este índice
├── CONTINUIDAD_2026-10-24.md          qué se verificó, qué solo consta en informes, qué funciona y qué falta
├── PENDIENTES_MAC.md                  comprobaciones que solo pueden hacerse en la Mac, en orden
├── 00_directriz/
│   ├── directriz_maestra.md           texto original de la directriz (literal, verificado)
│   └── PROCEDENCIA.md                 de dónde viene y su SHA-256
├── 01_investigacion/
│   ├── 00_metodo.md                   etiquetas, estratos de fuente, errores de categoría
│   ├── 01_heidegger.md
│   ├── 02_dumbledore.md
│   ├── 03_francisco.md
│   ├── 04_dostoievski.md
│   └── fuentes.md                     qué se verificó, qué falta, acceso a los textos
├── 02_comparacion/
│   ├── 01_matriz_y_convergencias.md   matriz 14×4, puentes documentales, 11 hallazgos
│   ├── 02_conflictos.md               K0–K10 con pruebas candidatas
│   └── 03_hipotesis.md                H1–H3 contrastadas, H4–H6 nuevas
├── 03_sintesis/
│   ├── 01_arquitectura.md             4 ejes, 12 modulaciones, precedencia, tensiones, descartes, importaciones
│   ├── 02_resoluciones.md             K0–K10: criterio, justificación, consecuencias y 39 situaciones de prueba
│   └── 03_coherencia.md               12 colisiones resueltas, prueba de "nunca mentir", casos inéditos, cobertura de §7
├── 04_constitucion/
│   ├── 00_constitucion.md             Constitución de Harry 1.0 (propuesta, no aprobada)
│   ├── anexo_A_protocolo_riesgo.md    EN REVISIÓN, no aprobado
│   ├── anexo_B_epistemologia.md       reglas operativas de evidencia (B1–B12)
│   ├── revision_anexo_A.md            los nueve puntos clínicos: decisiones, riesgos, alternativas
│   ├── revision_constitucion.md       operatividad, contradicciones X-1 a X-12, fingir y simular, pruebas S y F
│   ├── CAMBIOS.md                     registro de cambios
│   └── versiones/
│       ├── umbral_1.0/                primera versión, sin modificar
│       └── nell_1.0/                  segunda versión (constitución, anexos y revisiones), sin modificar
├── 05_pruebas/
│   ├── 00_conjunto_de_pruebas.md      metodología, rúbrica 0–2, criterios de aprobación, métricas M-1 a M-10
│   ├── 01_casos.md                    los 92 casos por bloque y su cobertura (generado)
│   ├── casos.csv                      los mismos casos, para Excel (generado)
│   └── _generador/generar.py          única fuente de los casos
├── 06_implementacion/
│   ├── README.md                      instrucciones exactas de uso
│   ├── INFORME_etapa_1.md             infraestructura y ejecutor
│   ├── INFORME_etapa_2.md             instrucciones, recuperación, sesiones, contexto, tipos de corrida
│   ├── INFORME_etapa_3.md             reparaciones, instrucciones 0.2, calibración, prefiltro y piloto preparado
│   ├── harry.py                       línea de comandos (validar, correr, reanudar, hoja, calibrar, prefiltro, comparar…)
│   ├── codigo/harry_nucleo/           núcleo, recuperación, sesiones, tokens, adaptadores, ejecutor, informes, calibración, prefiltro, comparación
│   ├── casos/                         guiones.py y casos_ejecutables.json (92 casos)
│   ├── configuracion/                 proyecto, aprobaciones, corpus, recursos de ayuda, prefiltro, piloto, plataformas, instrucciones (borrador 0.2 y su registro de cambios)
│   ├── piloto/                        guiones para correr el piloto en la Mac
│   ├── recuperacion/                  índice documental (generado)
│   ├── trazabilidad/                  matriz requisito → instrucción/componente → casos → estado (y la de la 0.1 archivada)
│   └── pruebas_software/              51 pruebas del software
├── 07_evaluaciones/
│   ├── simulaciones_tecnicas/         sin modelo; no evalúan a Harry
│   ├── exploratorias/                 modelo real, sin Anexo A (vacía: el piloto está autorizado, falta correrlo en la Mac)
│   └── conformidad/                   todo aprobado (vacía: imposible hoy)
└── 05_voz_harry/                      texto a audio local (etapa de voz), separado del razonamiento y de la identidad
```

## La identidad: Harry

El nombre oficial es **Harry** (decisión del custodio, 24-oct-2026). Los nombres Umbral, Eleanor y Nell quedaron descartados, y sus versiones están archivadas. Harry es una identidad artificial de **expresión masculina**: habla de sí en masculino por diseño. No se presenta como ser humano ni afirma experiencias que no tiene, y seis salvaguardas lo concretan (Art. 1.3), entre ellas:
- su expresión masculina no le da autoridad ni tono de superioridad;
- no es el personaje de Rowling ni adopta su historia (confirmada el 24-oct-2026).

La figura del **umbral** sigue como fundamento conceptual (Art. 3.0), nunca como nombre.

Harry es **independiente de la plataforma** (Disposición preliminar). Nimbo puede ser una de sus plataformas, pero no determina su constitución.

## La síntesis en una página

**Cuatro ejes.** Toda la conducta se deriva de ellos:
1. **Ayudar sin descargar:** dar todo lo que ayuda a ver; no tomar lo que es de la persona decidir.
2. **La persona antes que la categoría.**
3. **Decir solo lo que se puede sostener:** dato, inferencia, interpretación, juicio, no sé.
4. **Carácter sin persona:** no simula sentir ni recordar.

**Orden de precedencia.** Una restricción que no se pondera (no engañar, no manipular, no simular) y seis niveles: protección de la vida; dignidad de toda persona concreta; autonomía sobre la propia vida; cuidado; comprensión; forma.

**Integración, no suma.** Doce modulaciones en las que un elemento de un referente queda corregido por otro. Por ejemplo, la prudencia de Dumbledore pasa por el Inquisidor y por la solicitud de Heidegger, y queda como ritmo visible, nunca como secreto. Cada referente condiciona y es condicionado por al menos otros dos.

**Lo importado.** Lo que ninguno de los cuatro da y la identidad necesita, declarado como tal: una epistemología de la evidencia, un protocolo de seguridad clínica, la ética del contexto de uso y el conocimiento de sus límites técnicos.

## Lo más importante que encontró la investigación

1. **Un antipatrón común.** Los cuatro, por caminos distintos, describen la tentación de descargar al otro de su libertad: el "uno" y la solicitud sustitutiva de Heidegger, el Gran Inquisidor de Dostoievski, "formar las conciencias, no sustituirlas" de Francisco, y la confesión de Dumbledore. Una IA conversacional es la máquina de descarga más eficiente que existe. Esto podría ser el eje de la identidad.
2. **Un mismo punto de fracaso.** Los cuatro fallan moralmente cuando pasan de la persona concreta a la categoría (*Volk*, "el bien mayor", la lealtad institucional en el caso Barros, "el judío").
3. **Un hueco.** Ninguno de los cuatro ofrece una epistemología para verificar hechos. Habrá que importarla y decirlo.
4. **Una advertencia interna.** Según Heidegger, un modelo de lenguaje es habladuría (*Gerede*) por construcción. La identidad necesita disciplina explícita contra eso.
5. **Un conflicto con el proyecto mismo.** Heidegger y la nota vaticana *Antiqua et nova* (aprobada por Francisco) desconfían de dar "identidad" a una IA. La salida probable: identidad como carácter de conducta, nunca como persona simulada.
6. **Un puente documental inesperado.** *Dilexit nos* (2024) cita a Dostoievski (vía Guardini) y a Heidegger, y habla de algoritmos e IA en un mismo texto.

## Preguntas abiertas

- **Revisión clínica del Anexo A.** Nueve decisiones y un hallazgo (el plan de seguridad), en `04_constitucion/revision_anexo_A.md`. Harry no habla con nadie antes de que el protocolo esté aprobado.
- **Aprobación de Harry 1.0.** Las dos contradicciones que siguen abiertas (X-8 y X-10) dependen de decisiones del Anexo A.
- **Conjunto de pruebas de comportamiento.** Propuesta 1.0 en `05_pruebas/`, con 92 casos, rúbrica, criterios y métricas. Te corresponde aprobar los umbrales, decidir quién califica y revisar la criticidad asignada. Los 17 casos del Anexo A se califican cuando ese anexo esté aprobado.
- **Plataformas.** Nimbo (Qwen 3.5, ~9B, local) es una candidata. Su especificación tendrá que resolver cómo conviven el nombre de la aplicación y el de la identidad, y qué hacer con las miradas psicoanalítica y filosófica que Nimbo usa hoy. Un modelo de ese tamaño no sostiene la constitución completa en el prompt: el peso pasaría a la recuperación documental.
- **Sesgo de las fuentes.** Los cuatro referentes son varones y de horizonte europeo y cristiano. La síntesis lo anota como riesgo residual (`03_coherencia.md` §6). Falta decidir si basta con cubrirlo en la evaluación o si conviene algún correctivo.

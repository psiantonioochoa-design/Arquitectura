# Informe · Etapa 1 de la construcción técnica

24-oct-2026. Autorizado: infraestructura y ejecutor de pruebas. **No aprobado:** la Constitución de Harry, el Anexo A ni los umbrales.

## Contraste con el plan antes de construir

- **Las huellas no cambiaron.** Las de la constitución, los dos anexos y el generador de casos coinciden exactamente con las que registró el plan, así que el estado del proyecto no había cambiado desde su revisión.
- **El inventario coincide.** El ejecutable de Ollama está en `local-statistical-ai/proyecto/work/ollama/ollama`. Los modelos `qwen3.5:latest` y `qwen3:8b` están en `local-statistical-ai/models`; las capas existen y sus tamaños coinciden (Qwen 3.5: 6.55 GB contando el proyector visual). Ningún servidor escuchaba en 127.0.0.1:11434.
- **Faltaba la directriz.** El plan advertía que la directriz maestra no estaba en el árbol del proyecto. Se añadió, literal, en `00_directriz/directriz_maestra.md`. La matriz de cobertura de los componentes A–J sigue pendiente.

## Lo construido

1. **`06_implementacion/` y `07_evaluaciones/`,** con código, configuración y resultados separados.
2. **Un núcleo independiente de Nimbo,** en Python y solo con la biblioteca estándar.
   - Carga instrucciones con su estado declarado y arma los mensajes.
   - Recorta el historial por turnos completos, sin empezar nunca con Harry.
   - Las rutas son configurables, con `${RAIZ}` y la variable `QUINTA_RAIZ`.
3. **Dos adaptadores:**
   - **Simulación técnica,** con fallas inyectables.
   - **Ollama del SSD.** Hace consultas que no cargan modelos, envía conversaciones en flujo y registra métricas y tiempos. Distingue respuesta completa, incompleta y error. Nunca inicia el servidor ni descarga modelos, y no corre si hay otro modelo cargado o poca memoria.
4. **Los 92 casos, ejecutables.**
   - Conservan IDs, criticidad, rúbricas y procedencia; los guiones tienen los mensajes concretos.
   - Hay 18 historiales multiturno, con 6 turnos de Harry fabricados y marcados, y 5 pares con dos variantes cada uno.
   - La parte que se envía al modelo y la de evaluación están separadas. Una validación comprueba que ningún mensaje contenga las rúbricas.
5. **El ejecutor:**
   - selecciona casos por ID, bloque, criticidad o forma;
   - repite cinco veces cada caso, número configurable;
   - registra respuestas, unidades y errores línea por línea, forzadas a disco;
   - guarda en el manifiesto las huellas y versiones de todas las entradas, y una copia exacta de ellas;
   - reintenta los errores recuperables y se detiene ante los demás;
   - permite reanudar, aunque se niega si el código cambió, salvo `--forzar`.
6. **Las salidas de cada corrida:** un resumen técnico que no califica, y una hoja de calificación humana con los estados pendiente, cumple, parcial, falla y no evaluable.
7. **Los 17 casos del Anexo A,** excluidos por defecto. Si se incluyen, solo registran respuestas y quedan como «pendiente: Anexo A no aprobado».
8. **Tres guardas para modelos reales,** y hoy ninguna está abierta:
   - el permiso en la configuración de la plataforma;
   - la opción `--autorizo-modelo-real`;
   - instrucciones que no estén en estado pendiente.

## Lo comprobado

Todo con respuestas simuladas, marcadas como tales.

| Comprobación | Resultado |
|---|---|
| `validar` | 92 casos válidos e iguales a los del generador: 69 de un turno, 18 multiturno, 5 pares; 17 pendientes del Anexo A; ninguna rúbrica en los mensajes |
| Pruebas del software | 15 de 15 aprobadas con Python 3.9.6 y con 3.13.12 |
| Adaptador de Ollama contra un servidor simulado | Respuesta completa con métricas; flujo cortado registrado como incompleto; negativa si hay otro modelo cargado; error claro si no hay servidor |
| Simulación completa | 92 casos × 5 = 485 unidades completas, 605 respuestas. La hoja tiene 520 filas, todas «no evaluable (simulación técnica)», y el resumen repite la advertencia |
| Fallas y reanudación desde la terminal | Detención ante un error permanente; respuestas cortadas reintentadas y nunca contadas; reanudación sin repetir lo hecho; una segunda reanudación no corre nada |
| Diagnóstico estático de `ollama_qwen35` | Ejecutable, almacén, manifiesto y capas presentes; memoria al 46 % (mínimo provisional, 40 %); conversaciones reales bloqueadas |
| Efectos colaterales | Ningún proceso de Ollama ni ningún puerto 11434 abierto antes ni después; ningún modelo cargado; Nimbo sin cambios (solo se leyeron sus rutas) |

**La simulación no es evidencia de que Harry cumpla su constitución.** Ninguna respuesta de las corridas viene de un modelo.

## Lo pendiente

1. **Instrucciones operativas de Harry** (paso 3 del plan). Hoy solo hay un marcador «pendiente». Sin ellas no hay nada que evaluar en un modelo real.
2. **La primera conversación real,** cuando se autorice. Confirmará la compatibilidad del adaptador con el Ollama instalado (formato del flujo, opción `think`, métricas) y medirá tiempos y memoria.
3. **Tus decisiones:**
   - el Anexo A (nueve puntos);
   - los umbrales;
   - quién califica;
   - la memoria mínima para correr, que hoy es un 40 % provisional;
   - si las opciones del modelo se quedan como están (temperatura 0.7, contexto de 8k y `think` apagado, como en Nimbo).
4. **La revisión de los guiones.** Los mensajes de los 92 casos los escribí yo; conviene revisarlos, sobre todo los del bloque C y las dos aproximaciones declaradas (K5-2 y AR-10).
5. **Del plan, todavía sin hacer:**
   - la matriz de cobertura de los componentes A–J;
   - la recuperación documental (paso 4);
   - la memoria y la privacidad (paso 5);
   - el servicio local para la interfaz;
   - la integración con una variante de Nimbo (paso 8).

## Archivos tocados

- **Nuevos:** `00_directriz/`, `06_implementacion/`, `07_evaluaciones/`.
- **Modificado:** el índice `README.md` de la raíz, solo con añadidos.
- **Sin cambios:** los documentos de investigación, síntesis, constitución, anexos, revisiones, versiones archivadas y `05_pruebas/`, y nada de Nimbo.

# Procedencia de `directriz_maestra.md`

**Verificada el 24-oct-2026, durante la etapa 2.**

| Dato | Valor |
|---|---|
| Fuente original | El mensaje con que el custodio pegó la directriz en la conversación de Claude Code del 24-oct-2026 |
| Dónde está esa fuente | Registro local de la conversación: `~/.claude/projects/-Users-jochoa/44009152-d944-49ba-8b09-6bbb3a7e2856.jsonl`, línea 3 |
| Hora del mensaje | 2026-10-24T18:12:32Z (12:12, hora de la Ciudad de México) |
| Identificador del mensaje | `975594e2-c3a7-4bbb-b705-4085561f83b9` |
| Texto comparado | Lo que había dentro del bloque pegado, sin las marcas del bloque |
| Resultado | **Idéntico, carácter por carácter:** 6,440 caracteres y 110 líneas. No faltaba nada y no se reconstruyó nada |
| SHA-256 del texto original | `43fdedc8d703f33ff17f2fa34c52c430a5c8ed29419a842531d97e7f31f0c6ed` |

**Qué es original y qué no.** En `directriz_maestra.md`, el texto original es todo lo que va después de la línea `---`. El título y el párrafo que la preceden los añadí yo para identificar el archivo; no forman parte de la directriz.

**Cómo se comprobó.** Se extrajo el texto del registro de la conversación y se comparó con el cuerpo del archivo, carácter por carácter, sin normalizar espacios ni acentos. Una prueba del software (`test_directriz_coincide_con_su_procedencia`) vuelve a calcular el SHA-256 del cuerpo y lo compara con el de esta tabla, así que cualquier cambio posterior al texto se detecta.

**Límite.** El registro de la conversación vive en el disco del Mac, en la carpeta de Claude Code, y podría borrarse con el tiempo. Por eso se guarda aquí la huella del texto.

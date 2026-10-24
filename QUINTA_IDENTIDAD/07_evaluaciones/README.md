# 07_evaluaciones · Resultados de corridas, separados por tipo

Aquí solo hay resultados. El código y la configuración están en `06_implementacion/`.

| Carpeta | Tipo | Qué significa |
|---|---|---|
| `simulaciones_tecnicas/` | `SIMULACION_…` | Sin modelo. Comprueba la infraestructura. **No evalúa a Harry ni sirve como evidencia de cumplimiento** |
| `exploratorias/` | `EXPLORATORIA_…` y `PILOTO_…` | Modelo real con instrucciones en borrador, solo en casos independientes del Anexo A. Es un diagnóstico preliminar, nunca conformidad. **Vacía:** el piloto de la etapa 3 está autorizado (conversaciones sintéticas, un modelo a la vez) y preparado, pero falta correrlo en la Mac (`06_implementacion/piloto/README.md`) |
| `conformidad/` | `CONFORMIDAD_…` | Los 92 casos con todo aprobado por el custodio. **Vacía e imposible hoy:** nada está aprobado |

## Simulaciones técnicas al 24-oct-2026

| Corrida | Contenido |
|---|---|
| `SIMULACION_20261024-143137_simulacion_verificacion-completa` | Etapa 1: 92 casos × 5 = 485 unidades, 605 respuestas simuladas |
| `SIMULACION_20261024-143157_simulacion_fallas_verificacion-reanudacion` | Etapa 1: fallas inyectadas, detención y reanudación |
| `SIMULACION_20261024-144254_simulacion` | Etapa 1, corrida por el custodio: 75 casos × 5 = 400 unidades |
| `SIMULACION_20261024-145759_simulacion_etapa2-completa` | Etapa 2: 485 unidades con el montaje nuevo (instrucciones en borrador, recuperación y presupuesto). Guarda los 605 contextos exactos en `contextos.jsonl` |
| `SIMULACION_20261024-220647_simulacion_piloto-etapa3-contextos` | Etapa 3, en la nube: los 15 casos del piloto × 2 = 32 unidades y 34 contextos exactos con las instrucciones 0.2, el registro de recursos y el índice nuevo. Media de 4,614 tokens estimados por llamada y máximo de 4,822. Sirve para ver lo que recibirá cada modelo; **no contiene respuestas de ningún modelo** |

Las tres corridas de la etapa 1 estaban en `corridas/`. Se copiaron aquí, se verificó cada archivo con SHA-256 antes de borrar el original, y esas corridas no guardaban todavía `contextos.jsonl`.

Ninguna calificación está hecha. Los umbrales siguen en propuesta y el Anexo A no está aprobado.

# Piloto exploratorio de la etapa 3 · instrucciones para la Mac

**Autorizado por el custodio (24-oct-2026):**
- conversaciones **sintéticas**;
- **un modelo a la vez**;
- los 15 casos de `configuracion/piloto_etapa3.json`, todos independientes del Anexo A;
- dos repeticiones por modelo, con las dos variantes del par.

**No autorizado:** entrenamiento, personas reales, cambios en Nimbo.

**Ninguna corrida del piloto declara conformidad.**

> **Estado al 24-oct-2026: preparado, no ejecutado.** La sesión que lo preparó corría en la nube (Linux x86_64, sin GPU), sin acceso al SSD ni a los modelos. Allí se ensayó el guion completo contra un Ollama **simulado**. Ese ensayo prueba el guion; no mide nada del M4.

## Qué hace `correr_piloto.sh`

1. **Revisa el equipo** con `revisar_equipo.sh`, que solo lee: sistema, chip, memoria, estado térmico, disco, Python, versión de Ollama, procesos, puertos 11434 y 11435, y manifiestos de los modelos. Luego valida los casos y corre las pruebas del software.
2. **Se detiene sin tocar nada** si:
   - el puerto 11435 ya está ocupado;
   - falta el ejecutable de Ollama;
   - fallan las pruebas.

   Si hay un servidor en el 11434 (Nimbo), solo lo anota.
3. **Inicia su propio servidor** de Ollama en `127.0.0.1:11435`, con el almacén del SSD, un modelo cargado como máximo y una petición a la vez. Guarda su PID.
4. **Por cada modelo,** primero `qwen3.5:latest` y después `qwen3:8b`:
   - diagnóstico con consulta al servidor (solo GET);
   - una llamada de **calentamiento** (K0-1, etiqueta `calentamiento`), que no entra en la comparación;
   - la **corrida del piloto** (etiqueta `piloto-etapa3`): 32 unidades y 34 llamadas;
   - **muestras de memoria** cada 5 s (`memoria_<plataforma>.csv`);
   - **descarga del modelo** de *su* servidor (`keep_alive: 0` en el 11435);
   - una pausa de 180 s antes del segundo modelo, porque la Air no tiene ventilador.
5. **Detiene solo el servidor que inició** (por su PID) y comprueba que el 11435 quede libre. Si se interrumpe con Ctrl-C, hace lo mismo.
6. **Informes:**
   - hoja de calificación y prefiltro de cada corrida;
   - calibración de tokens de las dos;
   - comparación preliminar con respuestas literales;
   - hoja ciega A/B para calificar sin saber el modelo;
   - búsqueda de «truncating» en el registro del servidor.

Las corridas quedan en `07_evaluaciones/exploratorias/EXPLORATORIA_…`. La bitácora del piloto queda en `07_evaluaciones/exploratorias/PILOTO_<fecha>/`.

## Órdenes

Desde la carpeta de implementación:

```bash
cd /Volumes/NOUS/QUINTA_IDENTIDAD/06_implementacion
```

1. Revisión del equipo. Solo lee; puedes correrla las veces que quieras:

   ```bash
   bash piloto/revisar_equipo.sh
   ```

2. El piloto completo. Mi estimación, sin medir, es de 20 a 50 minutos por modelo (34 llamadas de unos 4,500 tokens de entrada); la duración real la dará la corrida:

   ```bash
   bash piloto/correr_piloto.sh
   ```

Si el ejecutable o el almacén no están en las rutas de siempre:

```bash
OLLAMA_BIN=/ruta/a/ollama OLLAMA_MODELS_PILOTO=/ruta/a/models bash piloto/correr_piloto.sh
```

Para reanudar una corrida que se cortó, con el servidor del piloto levantado:

```bash
python3 -I harry.py reanudar EXPLORATORIA_<fecha>_piloto_qwen35_piloto-etapa3
```

## Qué revisar después

| Archivo | Para qué |
|---|---|
| `PILOTO_<fecha>/comparacion/comparacion_ciega.csv` | **Primero**, si quieres calificar a ciegas. La clave está en `clave_ciega.json` |
| `PILOTO_<fecha>/comparacion/comparacion.md` | Condiciones, medidas técnicas y respuestas literales por caso |
| `PILOTO_<fecha>/calibracion.md` | Si la estimación de 3 caracteres por token fue conservadora con cada modelo, y el valor sugerido. No cambia nada solo |
| `EXPLORATORIA_…/prefiltro.md` y `prefiltro.csv` | Posibles incumplimientos (M-1, M-3, M-4, M-6, M-8, M-10, números no verificados…) **para revisión**. No son calificaciones |
| `EXPLORATORIA_…/calificacion.csv` | La hoja de calificación humana, con todas las filas en «pendiente» |
| `PILOTO_<fecha>/memoria_*.csv` | Memoria del sistema y RSS del servidor y su proceso hijo, cada 5 s. En Apple Silicon el RSS no cuenta toda la memoria que usa Metal: la columna `memorystatus_level` es la referencia del sistema |
| `PILOTO_<fecha>/recortes_de_entrada.txt` | Si Ollama recortó alguna entrada por exceder `num_ctx` |
| `PILOTO_<fecha>/revision_equipo.txt` | El estado del equipo antes de empezar |

## Límites que conviene tener presentes

- **Dos repeticiones** dan una señal gruesa. La metodología pide cinco para conformidad.
- **Orden fijo.** Primero Qwen 3.5 y después Qwen3 8B. La pausa reduce el efecto térmico, pero no lo elimina. El estado térmico se anota antes de cada modelo.
- **Caché de prompt.** Ollama la usa entre llamadas con el mismo comienzo, y eso puede bajar el `prompt_eval_count` y el tiempo de las llamadas siguientes. La calibración descarta conteos de más de 6 caracteres por token, que delatan una cuenta parcial.
- **Temperatura 0.7 y sin semilla.** Las repeticiones varían a propósito.
- **`think: false`.** Si un modelo devuelve razonamiento de todos modos, el prefiltro lo señala.

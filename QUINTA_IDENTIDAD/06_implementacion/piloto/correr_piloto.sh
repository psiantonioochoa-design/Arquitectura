#!/bin/bash
# Piloto exploratorio de la etapa 3, en la Mac del custodio.
#
# Autorizado (24-oct-2026): conversaciones SINTÉTICAS, un modelo a la vez, los 15 casos de
# configuracion/piloto_etapa3.json, dos repeticiones por modelo. No autorizado: entrenamiento,
# personas reales, cambios en Nimbo. Ninguna corrida declara conformidad.
#
# Qué hace, en orden:
#   1. Revisa el equipo (solo lectura) y se detiene si el puerto 11435 está ocupado, si falta
#      un modelo o si la memoria disponible es menor que la mínima de la plataforma.
#   2. Inicia SU PROPIO servidor de Ollama en 127.0.0.1:11435 (nunca el 11434 de Nimbo) y
#      guarda su PID.
#   3. Por cada modelo, uno a la vez: diagnóstico, una llamada de calentamiento, la corrida
#      del piloto, muestras de memoria cada 5 s, y descarga del modelo de SU servidor.
#   4. Detiene solo el servidor que inició (por su PID) y comprueba que el puerto quede libre.
#   5. Calibración de tokens, prefiltro, hojas de calificación y comparación preliminar.
#
# Uso:  cd /Volumes/NOUS/QUINTA_IDENTIDAD/06_implementacion && bash piloto/correr_piloto.sh
# Variables opcionales: OLLAMA_BIN, OLLAMA_MODELS_PILOTO, PAUSA_ENTRE_MODELOS (segundos).

set -u
IMPL="$(cd "$(dirname "$0")/.." && pwd)"
RAIZ="$(cd "$IMPL/.." && pwd)"
OLLAMA_BIN="${OLLAMA_BIN:-/Volumes/NOUS/local-statistical-ai/proyecto/work/ollama/ollama}"
ALMACEN="${OLLAMA_MODELS_PILOTO:-/Volumes/NOUS/local-statistical-ai/models}"
HOST="127.0.0.1:11435"
URL="http://$HOST"
CFG="$IMPL/configuracion/piloto_etapa3.json"
SELLO="$(date '+%Y%m%d-%H%M%S')"
BITACORA="$RAIZ/07_evaluaciones/exploratorias/PILOTO_$SELLO"
mkdir -p "$BITACORA"
SERVIDOR_PID=""
MUESTREO_PID=""

dato() { python3 -I -c "import json,sys; v=json.load(open(sys.argv[1]))[sys.argv[2]]; print(','.join(v) if isinstance(v,list) else v)" "$CFG" "$1"; }
anota() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$BITACORA/bitacora.txt"; }

CASOS="$(dato casos)"
REPETICIONES="$(dato repeticiones)"
PLATAFORMAS="$(dato plataformas_en_orden | tr ',' ' ')"
PAUSA="${PAUSA_ENTRE_MODELOS:-$(dato pausa_entre_modelos_s)}"
CAL_CASO="$(python3 -I -c "import json,sys; print(json.load(open(sys.argv[1]))['calentamiento']['caso'])" "$CFG")"

modelo_de() { python3 -I -c "import json,sys; print(json.load(open(sys.argv[1]))['adaptador']['modelo'])" "$IMPL/configuracion/plataformas/$1.json"; }

descargar_modelo() {  # solo en NUESTRO servidor (11435)
  curl -s --max-time 30 "$URL/api/generate" -d "{\"model\": \"$1\", \"keep_alive\": 0}" >/dev/null 2>&1 || true
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if ! curl -s --max-time 3 "$URL/api/ps" | grep -q "\"$1\""; then return 0; fi
    sleep 1
  done
  anota "AVISO: $1 sigue cargado en $HOST tras 10 s"
}

limpiar() {
  [ -n "$MUESTREO_PID" ] && kill "$MUESTREO_PID" 2>/dev/null
  if [ -n "$SERVIDOR_PID" ] && kill -0 "$SERVIDOR_PID" 2>/dev/null; then
    for p in $PLATAFORMAS; do descargar_modelo "$(modelo_de "$p")"; done
    anota "Deteniendo SOLO el servidor del piloto (PID $SERVIDOR_PID, $HOST)"
    kill "$SERVIDOR_PID" 2>/dev/null
    for _ in 1 2 3 4 5 6 7 8 9 10; do kill -0 "$SERVIDOR_PID" 2>/dev/null || break; sleep 1; done
    kill -0 "$SERVIDOR_PID" 2>/dev/null && anota "AVISO: el servidor $SERVIDOR_PID no terminó; revísalo a mano"
  fi
  if lsof -nP -iTCP:11435 -sTCP:LISTEN >/dev/null 2>&1; then anota "AVISO: el puerto 11435 sigue ocupado"; else anota "Puerto 11435 libre"; fi
}
trap limpiar EXIT
trap 'anota "Interrumpido por el usuario"; exit 130' INT TERM

muestrear_memoria() {  # cada 5 s: memoria del sistema y RSS del servidor del piloto y sus hijos
  echo "hora,etiqueta,memorystatus_level_pct,rss_servidor_y_runner_mb,physmem" > "$BITACORA/memoria_$1.csv"
  while true; do
    pids="$SERVIDOR_PID $(pgrep -P "$SERVIDOR_PID" 2>/dev/null | tr '\n' ' ')"
    rss=0; for p in $pids; do r=$(ps -o rss= -p "$p" 2>/dev/null | tr -d ' '); rss=$(( rss + ${r:-0} )); done
    pm=$(top -l 1 -s 0 2>/dev/null | grep '^PhysMem' | tr ',' ';')
    echo "$(date '+%H:%M:%S'),$1,$(sysctl -n kern.memorystatus_level 2>/dev/null),$(( rss / 1024 )),\"$pm\"" >> "$BITACORA/memoria_$1.csv"
    sleep 5
  done
}

ultima_corrida() {  # carpeta más reciente de exploratorias con el texto dado
  ls -1dt "$RAIZ/07_evaluaciones/exploratorias/EXPLORATORIA_"*"$1"* 2>/dev/null | head -1
}

# ------------------------------------------------------------------ 1. revisión
anota "Piloto de la etapa 3. Bitácora: $BITACORA"
anota "Casos: $CASOS · repeticiones: $REPETICIONES · plataformas: $PLATAFORMAS"
bash "$IMPL/piloto/revisar_equipo.sh" "$BITACORA" >/dev/null
python3 -I "$IMPL/harry.py" validar | tee -a "$BITACORA/bitacora.txt" || { anota "ERROR: casos inválidos"; exit 1; }
python3 -I -m unittest discover -s "$IMPL/pruebas_software" > "$BITACORA/pruebas_software.txt" 2>&1 \
  || { anota "ERROR: fallan pruebas del software (ver pruebas_software.txt)"; exit 1; }
[ -x "$OLLAMA_BIN" ] || { anota "ERROR: no encuentro $OLLAMA_BIN"; exit 1; }
if lsof -nP -iTCP:11435 -sTCP:LISTEN >/dev/null 2>&1; then
  anota "ERROR: el puerto 11435 ya está ocupado por otro proceso. No se toca; el piloto no empieza."; exit 1
fi
if lsof -nP -iTCP:11434 -sTCP:LISTEN >/dev/null 2>&1; then
  anota "Nota: hay un servidor en 11434 (probablemente Nimbo). No se toca. Modelos cargados allí: $(curl -s --max-time 3 http://127.0.0.1:11434/api/ps)"
fi
"$OLLAMA_BIN" --version > "$BITACORA/version_ollama.txt" 2>&1 || true

# ------------------------------------------------------------------ 2. servidor propio
anota "Iniciando servidor del piloto en $HOST"
OLLAMA_MODELS="$ALMACEN" OLLAMA_HOST="$HOST" OLLAMA_NO_CLOUD=1 OLLAMA_MAX_LOADED_MODELS=1 \
  OLLAMA_NUM_PARALLEL=1 OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0 \
  nohup "$OLLAMA_BIN" serve > "$BITACORA/servidor.log" 2>&1 &
SERVIDOR_PID=$!
echo "$SERVIDOR_PID" > "$BITACORA/servidor.pid"
for _ in $(seq 1 60); do curl -s --max-time 2 "$URL/api/version" >/dev/null 2>&1 && break; sleep 1; done
curl -s --max-time 2 "$URL/api/version" > "$BITACORA/version_servidor.json" || { anota "ERROR: el servidor no respondió en 60 s"; exit 1; }
anota "Servidor listo (PID $SERVIDOR_PID): $(cat "$BITACORA/version_servidor.json")"

# ------------------------------------------------------------------ 3. un modelo a la vez
CORRIDAS=""
primero=1
for plat in $PLATAFORMAS; do
  modelo="$(modelo_de "$plat")"
  if [ $primero -eq 0 ]; then anota "Pausa de $PAUSA s entre modelos"; sleep "$PAUSA"; fi
  primero=0
  anota "== $plat ($modelo) · estado térmico: $(pmset -g therm 2>/dev/null | tr '\n' ' ')"
  python3 -I "$IMPL/harry.py" diagnostico --plataforma "$plat" --consultar-servidor > "$BITACORA/diagnostico_$plat.txt" 2>&1 \
    || { anota "ERROR en el diagnóstico de $plat (ver diagnostico_$plat.txt)"; exit 1; }
  muestrear_memoria "$plat" & MUESTREO_PID=$!
  anota "Calentamiento: $CAL_CASO, 1 repetición (no entra en la comparación)"
  python3 -I "$IMPL/harry.py" correr --plataforma "$plat" --casos "$CAL_CASO" --repeticiones 1 \
    --autorizo-modelo-real --etiqueta "calentamiento" >> "$BITACORA/bitacora.txt" 2>&1 \
    || { anota "ERROR en el calentamiento de $plat: se detiene el piloto"; exit 1; }
  anota "Corrida del piloto: $plat"
  python3 -I "$IMPL/harry.py" correr --plataforma "$plat" --casos "$CASOS" --repeticiones "$REPETICIONES" \
    --autorizo-modelo-real --etiqueta "piloto-etapa3" 2>&1 | tee -a "$BITACORA/bitacora.txt"
  codigo=${PIPESTATUS[0]}
  [ "$codigo" -eq 0 ] || anota "AVISO: la corrida de $plat terminó con código $codigo (3 = detenida o con pendientes); se sigue con el siguiente modelo y queda anotado"
  kill "$MUESTREO_PID" 2>/dev/null; MUESTREO_PID=""
  c="$(ultima_corrida "${plat}_piloto-etapa3")"
  [ -n "$c" ] && CORRIDAS="$CORRIDAS $c"
  anota "Descargando $modelo del servidor del piloto"
  descargar_modelo "$modelo"
done

# ------------------------------------------------------------------ 4. liberar lo nuestro
limpiar
trap - EXIT

# ------------------------------------------------------------------ 5. informes
grep -in 'truncat' "$BITACORA/servidor.log" > "$BITACORA/recortes_de_entrada.txt" 2>/dev/null \
  && anota "AVISO: el servidor registró recortes de entrada (ver recortes_de_entrada.txt)" \
  || anota "El servidor no registró recortes de entrada"
for c in $CORRIDAS; do
  python3 -I "$IMPL/harry.py" hoja "$c" >> "$BITACORA/bitacora.txt"
  python3 -I "$IMPL/harry.py" prefiltro "$c" > /dev/null
done
# shellcheck disable=SC2086
python3 -I "$IMPL/harry.py" calibrar $CORRIDAS --destino "$BITACORA" > /dev/null
# shellcheck disable=SC2086
python3 -I "$IMPL/harry.py" comparar $CORRIDAS --destino "$BITACORA/comparacion" | tee -a "$BITACORA/bitacora.txt"
anota "Listo. Corridas: $CORRIDAS"
anota "Revisa: $BITACORA/comparacion/comparacion.md (o califica antes a ciegas con comparacion_ciega.csv),"
anota "        $BITACORA/calibracion.md, prefiltro.md de cada corrida y memoria_*.csv."
anota "Nada de esto es conformidad: el Anexo A y la constitución siguen sin aprobar."

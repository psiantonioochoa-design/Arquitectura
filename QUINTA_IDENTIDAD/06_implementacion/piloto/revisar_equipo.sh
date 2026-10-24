#!/bin/bash
# Revisión del equipo antes del piloto. SOLO LEE: no inicia ni detiene nada,
# no cierra aplicaciones, no carga modelos y no toca Nimbo.
#
# Uso:  bash 06_implementacion/piloto/revisar_equipo.sh [carpeta_de_salida]
# Escribe revision_equipo.txt en la carpeta indicada (o la muestra en pantalla).

set -u
IMPL="$(cd "$(dirname "$0")/.." && pwd)"
OLLAMA_BIN="${OLLAMA_BIN:-/Volumes/NOUS/local-statistical-ai/proyecto/work/ollama/ollama}"
ALMACEN="${OLLAMA_MODELS_PILOTO:-/Volumes/NOUS/local-statistical-ai/models}"
SALIDA="${1:-}"

revisar() {
  echo "== Revisión del equipo · $(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "-- Sistema"
  sw_vers 2>/dev/null || uname -a
  echo "Arquitectura: $(uname -m)"
  echo "Chip: $(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo desconocido)"
  echo "Memoria física: $(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 )) GB"
  echo "Nivel de memoria disponible (kern.memorystatus_level): $(sysctl -n kern.memorystatus_level 2>/dev/null || echo desconocido) %"
  echo "-- Memoria (top, una muestra)"
  top -l 1 -s 0 2>/dev/null | grep -E '^(PhysMem|VM|Swap)' || true
  echo "-- vm_stat"
  vm_stat 2>/dev/null | head -12 || true
  echo "-- Estado térmico"
  pmset -g therm 2>/dev/null || echo "pmset no disponible"
  echo "-- Disco"
  df -h /Volumes/NOUS 2>/dev/null || echo "No está montado /Volumes/NOUS"
  echo "-- Python"
  command -v python3 && python3 --version
  echo "-- Ollama del SSD"
  if [ -x "$OLLAMA_BIN" ]; then
    # Con un puerto sin servidor, la orden solo informa la versión del cliente.
    OLLAMA_HOST=127.0.0.1:1 "$OLLAMA_BIN" --version 2>&1 | head -3
  else
    echo "No encuentro el ejecutable: $OLLAMA_BIN"
  fi
  echo "Almacén de modelos: $ALMACEN $( [ -d "$ALMACEN" ] && echo '(existe)' || echo '(NO EXISTE)')"
  echo "-- Procesos de Ollama (solo se listan)"
  ps -axo pid,ppid,rss,etime,command 2>/dev/null | grep -i '[o]llama' || echo "ninguno"
  echo "-- Puertos"
  for p in 11434 11435; do
    if lsof -nP -iTCP:$p -sTCP:LISTEN >/dev/null 2>&1; then
      echo "Puerto $p: ESCUCHANDO"
      lsof -nP -iTCP:$p -sTCP:LISTEN 2>/dev/null | tail -n +2
      echo "   Modelos cargados en $p (GET /api/ps, no carga nada): $(curl -s --max-time 3 http://127.0.0.1:$p/api/ps || echo 'sin respuesta')"
    else
      echo "Puerto $p: libre"
    fi
  done
  echo "-- Plataformas del piloto (diagnóstico estático, sin servidor)"
  for plat in piloto_qwen35 piloto_qwen3_8b; do
    python3 -I "$IMPL/harry.py" diagnostico --plataforma "$plat" | grep -E 'ERROR|AVISO|Manifiesto|Memoria|Instrucciones:' || true
  done
  echo "-- Fin de la revisión (no se cambió nada)"
}

if [ -n "$SALIDA" ]; then
  mkdir -p "$SALIDA"
  revisar 2>&1 | tee "$SALIDA/revision_equipo.txt"
else
  revisar 2>&1
fi

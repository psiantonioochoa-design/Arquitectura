#!/bin/bash
# Revisión del equipo para la voz de Harry. SOLO LEE: no instala, no descarga, no cambia nada.
# Uso:  bash instalar/revisar_equipo.sh   (desde 05_voz_harry). Guarda una copia en evaluacion/registros/.

set -u
VOZ="$(cd "$(dirname "$0")/.." && pwd)"
SALIDA="$VOZ/evaluacion/registros/revision_equipo_$(date '+%Y%m%d-%H%M%S').txt"
mkdir -p "$(dirname "$SALIDA")"

{
echo "== Revisión del equipo para la voz · $(date '+%Y-%m-%d %H:%M:%S %z')"
echo "-- Sistema"
sw_vers 2>/dev/null || uname -a
echo "Arquitectura: $(uname -m) · Chip: $(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo desconocido)"
echo "Memoria física: $(( $(sysctl -n hw.memsize 2>/dev/null || echo 0) / 1073741824 )) GB · disponible (memorystatus_level): $(sysctl -n kern.memorystatus_level 2>/dev/null || echo ¿?) %"
top -l 1 -s 0 2>/dev/null | grep -E '^PhysMem' || true
echo "-- Disco donde está 05_voz_harry"
df -h "$VOZ" | tail -1
echo "Longitud de la ruta de 05_voz_harry: ${#VOZ} caracteres (eSpeak NG no admite rutas de datos de más de 230)"
echo "-- Python y herramientas"
for p in python3 python3.12 python3.11 python3.10 uv ffmpeg git; do
  if command -v "$p" >/dev/null 2>&1; then echo "$p: $(command -v "$p") · $("$p" --version 2>&1 | head -1)"; else echo "$p: no está"; fi
done
if command -v ffmpeg >/dev/null 2>&1; then
  ffmpeg -hide_banner -filters 2>/dev/null | grep -q " rubberband " && echo "ffmpeg con rubberband: sí (cambio de tono con formantes preservados)" || echo "ffmpeg con rubberband: no (se usará otro método de posproceso)"
fi
echo "-- Motores de voz ya instalados en los Python del sistema (solo se consulta)"
for p in python3 python3.12 python3.11; do
  command -v "$p" >/dev/null 2>&1 || continue
  "$p" -c "import importlib.metadata as m
for d in ('piper-tts','kokoro','chatterbox-tts','torch','onnxruntime'):
    try: print('   $p', d, m.version(d))
    except Exception: pass" 2>/dev/null
done
echo "-- Pesos que ya existen en el equipo (para no copiarlos)"
for d in "$HOME/.cache/huggingface/hub" "${HF_HOME:-}/hub" "$VOZ/modelos/hf/hub"; do
  [ -d "$d" ] && ls -d "$d"/models--hexgrad--Kokoro-82M "$d"/models--ResembleAI--* 2>/dev/null | sed 's/^/   /'
done
find "$HOME/.local/share" "$HOME/Library/Application Support" /Volumes/NOUS -maxdepth 6 \
  \( -name 'en_GB-*.onnx' -o -name 'es_MX-*.onnx' -o -name 'es_ES-*.onnx' \) 2>/dev/null | head -20 | sed 's/^/   piper: /'
echo "-- Entornos del proyecto"
for m in piper kokoro chatterbox espeak_prueba; do
  [ -x "$VOZ/entornos/$m/bin/python" ] && echo "   $m: listo ($(du -sh "$VOZ/entornos/$m" | cut -f1))" || echo "   $m: no creado"
done
echo "-- Procesos pesados ahora (los 8 con más memoria; solo se listan)"
ps -axo rss,comm 2>/dev/null | sort -rn | head -8 | awk '{printf "   %6.0f MB  %s\n", $1/1024, $2}'
echo "-- Fin de la revisión (no se cambió nada)"
} 2>&1 | tee "$SALIDA"
echo "Copia: $SALIDA"

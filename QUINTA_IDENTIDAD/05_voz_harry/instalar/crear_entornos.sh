#!/bin/bash
# Crea el entorno de Python AISLADO de un motor, dentro de 05_voz_harry/entornos/<motor>.
# No instala nada fuera de 05_voz_harry: las cachés de uv y de pip, y el Python que
# descargue uv, quedan en 05_voz_harry/.cache/. No usa sudo ni Homebrew ni cambia el PATH.
# No descarga pesos de modelos (eso lo hace descargar_modelos.py, con autorización).
#
# Uso:  bash instalar/crear_entornos.sh <piper|kokoro|chatterbox|espeak_prueba> [--v3] [--autorizo-grande]
#   --v3               Chatterbox: instala el código de GitHub (Multilingual V3) en un commit fijo
#   --autorizo-grande  obligatorio para chatterbox (el entorno ocupa ~1.5–2 GB)

set -u
VOZ="$(cd "$(dirname "$0")/.." && pwd)"
MOTOR="${1:-}"; shift || true
V3=0; GRANDE=0
for a in "$@"; do case "$a" in --v3) V3=1;; --autorizo-grande) GRANDE=1;; *) echo "Opción desconocida: $a"; exit 2;; esac; done
case "$MOTOR" in piper|kokoro|chatterbox|espeak_prueba) ;; *) echo "Uso: $0 <piper|kokoro|chatterbox|espeak_prueba> [--v3] [--autorizo-grande]"; exit 2;; esac
if [ "$MOTOR" = chatterbox ] && [ $GRANDE -eq 0 ]; then
  echo "El entorno de Chatterbox ocupa ~1.5–2 GB (torch, transformers, gradio…). Repite con --autorizo-grande si lo autorizas."; exit 3
fi

ENT="$VOZ/entornos/$MOTOR"
REQ="$VOZ/instalar/requisitos/$MOTOR.txt"
export UV_CACHE_DIR="$VOZ/.cache/uv" PIP_CACHE_DIR="$VOZ/.cache/pip" UV_PYTHON_INSTALL_DIR="$VOZ/.cache/python"
PY_VER="3.12"

if [ -e "$ENT" ]; then echo "Ya existe $ENT. Bórralo a mano si quieres recrearlo."; exit 1; fi
if [ ${#ENT} -gt 120 ]; then
  echo "AVISO: la ruta $ENT es larga (${#ENT} caracteres). eSpeak NG no admite rutas de datos de más de 230; conviene una ruta corta."
fi

if command -v uv >/dev/null 2>&1; then
  echo "== Creando $ENT con uv (Python $PY_VER; si hace falta, uv lo descarga en $UV_PYTHON_INSTALL_DIR)"
  uv venv --seed --python "$PY_VER" "$ENT" || exit 1  # --seed: incluye pip (spacy download lo usa)
  instalar() { VIRTUAL_ENV="$ENT" uv pip install "$@"; }
elif command -v "python$PY_VER" >/dev/null 2>&1; then
  echo "== Creando $ENT con python$PY_VER -m venv"
  "python$PY_VER" -m venv "$ENT" || exit 1
  instalar() { "$ENT/bin/python" -m pip install "$@"; }
else
  echo "No hay uv ni python$PY_VER. Los motores necesitan Python 3.10–3.12 (el python3 del sistema, 3.9, no sirve)."
  echo "Opciones, a tu elección: instalar uv (https://docs.astral.sh/uv/) o Python 3.12 (python.org o Homebrew)."
  echo "Este guion no instala nada fuera de 05_voz_harry sin que lo decidas tú."
  exit 4
fi

if [ "$MOTOR" = chatterbox ] && [ $V3 -eq 1 ]; then
  COMMIT="$(git ls-remote https://github.com/resemble-ai/chatterbox HEAD | cut -f1)"
  [ -n "$COMMIT" ] || { echo "No pude leer el commit de GitHub"; exit 1; }
  echo "== Chatterbox desde GitHub, commit $COMMIT (Multilingual V3)"
  instalar "chatterbox-tts @ git+https://github.com/resemble-ai/chatterbox@$COMMIT" || exit 1
else
  instalar -r "$REQ" || exit 1
fi

if [ "$MOTOR" = kokoro ]; then
  # misaki descarga en_core_web_sm la primera vez si no está; se instala ahora para trabajar sin conexión
  "$ENT/bin/python" -m spacy download en_core_web_sm || { echo "No se pudo instalar en_core_web_sm"; exit 1; }
fi

{
  echo "motor: $MOTOR"
  echo "fecha: $(date '+%Y-%m-%d %H:%M:%S %z')"
  echo "equipo: $(uname -sm) $(sysctl -n machdep.cpu.brand_string 2>/dev/null)"
  echo "python: $("$ENT/bin/python" --version 2>&1)"
  [ -n "${COMMIT:-}" ] && echo "chatterbox_commit: $COMMIT"
  echo "--- paquetes"
  if command -v uv >/dev/null 2>&1; then VIRTUAL_ENV="$ENT" uv pip freeze; else "$ENT/bin/python" -m pip freeze; fi
} > "$ENT/INSTALADO.txt"
du -sh "$ENT" | sed 's/^/Tamaño del entorno: /'
echo "Listo. Registro de versiones: $ENT/INSTALADO.txt"

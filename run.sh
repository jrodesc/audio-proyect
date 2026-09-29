#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
VENV_PYTHON="$VENV_DIR/bin/python"

echo "🎵 YouTube Audio Player"
echo "======================="

if ! command -v python3 >/dev/null 2>&1; then
    echo "Error: Python 3 no está instalado."
    exit 1
fi

# Un entorno existente puede estar incompleto (por ejemplo, tener el lanzador
# pip pero no el módulo pip). En ese caso se reconstruye antes de instalar.
if [[ ! -x "$VENV_PYTHON" ]] || ! "$VENV_PYTHON" -m pip --version >/dev/null 2>&1; then
    echo "📦 Creando/reparando el entorno virtual..."
    if ! python3 -m venv --clear "$VENV_DIR"; then
        echo "Error: no se pudo crear el entorno virtual."
        echo "Fedora: instala python3 y python3-pip."
        echo "Ubuntu/Mint: instala python3-venv y python3-pip."
        exit 1
    fi
fi

echo "📥 Comprobando dependencias..."
if ! "$VENV_PYTHON" -m pip install -q -r "$PROJECT_DIR/requirements.txt"; then
    echo "Error: no se pudieron instalar las dependencias; la app no se iniciará."
    exit 1
fi

if ! command -v mpv >/dev/null 2>&1; then
    echo "Aviso: mpv no está instalado; la reproducción de audio no estará disponible."
    case "${ID:-}:${ID_LIKE:-}" in
        *fedora*) echo "Instálalo con: sudo dnf install mpv" ;;
        *debian*|*ubuntu*) echo "Instálalo con: sudo apt install mpv" ;;
    esac
fi

echo "🚀 Iniciando la aplicación..."
cd "$PROJECT_DIR/src"
exec "$VENV_PYTHON" main.py

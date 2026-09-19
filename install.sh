#!/bin/bash
# zzoDrive installer for macOS and Linux
set -e

cd "$(dirname "$0")"

echo ""
echo "============================================================"
echo "        zzoDrive installer"
echo "============================================================"
echo ""

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found."
    echo "Install it from https://www.python.org/downloads/"
    exit 1
fi

echo "Using python3: $(python3 --version)"
echo ""

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

echo ""
echo "============================================================"
echo "  ✅ Installation complete!"
echo "============================================================"
echo ""
echo "  To start zzoDrive:"
echo ""
echo "      ./start.sh"
echo ""
echo "  Or simply:"
echo ""
echo "      source .venv/bin/activate"
echo "      python run.py"
echo ""

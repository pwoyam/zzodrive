#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "First run — installing dependencies..."
    bash install.sh
fi

source .venv/bin/activate
exec python run.py

#!/bin/bash
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "First run — installing dependencies..."
    bash install.sh
fi

source .venv/bin/activate

# Pre-import heavy modules while user waits (cached by OS)
python3 -c "import telethon, cryptography, flask" 2>/dev/null &

# Start server
exec python run.py

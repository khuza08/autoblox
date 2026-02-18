#!/bin/bash

# Script to run autoblox with Real-Time Priority

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PYTHON_BIN="$DIR/venv/bin/python"

if [ ! -f "$PYTHON_BIN" ]; then
    echo "[!] Error: Virtual environment python not found at $PYTHON_BIN"
    exit 1
fi

echo "[*] Launching with Real-Time Priority (chrt -f 99)..."
echo "[*] Password may be required for sudo access to hardware input devices."

# Launching with FIFO scheduler at max priority (99)
# This ensures the kernel prioritizes our timing loop above all else.
sudo chrt -f 99 "$PYTHON_BIN" "$DIR/gui.py"

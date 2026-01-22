#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ---- Backend ----
cd "$SCRIPT_DIR/backend"
python3 -m venv myvenv
source myvenv/bin/activate
pip install -r requirements.txt
# Start backend in background
python3 app.py &
BACKEND_PID=$!

# ---- Frontend ----
cd "$SCRIPT_DIR/frontend"
npm install
npm run dev

trap "kill $BACKEND_PID" EXIT
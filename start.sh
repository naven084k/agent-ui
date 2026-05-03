#!/usr/bin/env bash
set -euo pipefail

npm install
python3 -m venv .venv
source .venv/bin/activate
pip install -e ./backend
npm run dev

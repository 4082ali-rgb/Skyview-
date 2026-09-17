#!/bin/bash
cd "$(dirname "$0")"
python3 -m pip install -r requirements.txt || echo "Install Python from https://www.python.org/downloads/ then run SETUP again."
read -p "Press Enter to close"

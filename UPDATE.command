#!/bin/bash
cd "$(dirname "$0")"
curl -sSL -o skyview_je.py.new "https://raw.githubusercontent.com/4082ali-rgb/Skyview-/claude/modest-hamilton-ce205v/skyview_je.py" && mv -f skyview_je.py.new skyview_je.py && echo Updated. || echo "Update failed."
read -p "Press Enter to close"

#!/bin/bash
cd "$(dirname "$0")"
BASE=https://raw.githubusercontent.com/4082ali-rgb/Skyview-/claude/modest-hamilton-ce205v
for f in "skyview_je.py" "RUN.command" "SETUP.command" "ADD ACCOUNT.command" "SET JOURNAL NUMBER.command" "RESET JOURNAL NUMBER.command" "README.md"; do
  curl -sSL -o "$f.new" "$BASE/${f// /%20}" && mv -f "$f.new" "$f" && chmod +x "$f" && echo "  updated $f" || echo "  FAILED $f"
done
mkdir -p inbox output
echo "Done."
read -p "Press Enter to close"

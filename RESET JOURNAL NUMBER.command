#!/bin/bash
cd "$(dirname "$0")"
echo "This clears the stored journal number. The next RUN will ask you for a new one"
echo "instead of counting up automatically."
read -p "Type YES to confirm: " ok
if [ "$ok" = "YES" ]; then
  rm -f skyview_je_state.json
  echo "Cleared. Next RUN will ask for the journal number."
else
  echo "Cancelled - nothing changed."
fi
read -p "Press Enter to close"

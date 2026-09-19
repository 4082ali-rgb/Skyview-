# Inbox

Download the day's GL Summary and Trial Balance PDFs into this folder (any exact filenames
starting with `GLSummary` and `TrialBalance` are fine, e.g. `GLSummary_Sep01.pdf`).

Double-click **RUN**. It reads the two PDFs from here, writes the CSV to a dated subfolder of
`output/` (e.g. `output/2026-09-11/`), and moves the used PDFs into that same dated folder too,
so this folder is empty and ready for tomorrow.

(You can still drop the PDFs straight into the main project folder instead, the old way - RUN
falls back to looking there if this folder is empty.)

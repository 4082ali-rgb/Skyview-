# Skyview JE builder

Daily use is `python skyview_je.py <gl.pdf> <tb.pdf> [--journal N | --auto]`.
It needs no AI. Only read `SKYVIEW_JE_SPEC.md` when changing rules.

If asked to help with a STOP message: answer from the message alone; do
not ask for the PDFs unless the message is insufficient. Accounting
questions are decided by Imran, not inferred. Never guess an account
mapping or a sign.

Tests: `python -m pytest tests/` compares script output against
hand-built CSVs byte-for-byte.

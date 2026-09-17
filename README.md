# Skyview daily JE

One-time: install Python from https://www.python.org/downloads/ (tick "Add python.exe to PATH"), then double-click **SETUP**.

Every day:
1. Download the GL Summary and Trial Balance PDFs into this folder.
2. Double-click **RUN**.
3. First time it asks for the journal number. After that it counts up by itself and tells you the number it used.
4. Import the `JJ####_Skyview_MonDD.csv` it creates into QuickBooks.

If it says `STOP:` nothing was written. Read the message, fix the input, and run again.

To change the journal number: double-click **SET JOURNAL NUMBER**, type the number the next entry should use, Enter.

If a new account shows up on a report, the window asks which QuickBooks account to use. Type it exactly as it is in QBO and press Enter. It is saved in `extra_accounts.json` and never asked again. Press Enter with nothing to stop instead.

If Claude fixes something, double-click **UPDATE** to get the new version. Your PDFs, journal number and saved accounts are untouched.

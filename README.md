# Skyview daily JE

One-time: install Python from https://www.python.org/downloads/ (tick "Add python.exe to PATH"), then double-click **SETUP**.

Every day:
1. Download the GL Summary and Trial Balance PDFs into this folder.
2. Double-click **RUN**.
3. First time it asks for the journal number. After that it counts up by itself and tells you the number it used.
4. Import the `JJ####_Skyview_MonDD.csv` it creates into QuickBooks.

If it says `STOP:` nothing was written. Read the message, fix the input, and run again.

To change the journal number: double-click **SET JOURNAL NUMBER**, type the number the next entry should use, Enter.

If something on the report is not recognised (a new account, an unknown tender, an unusual CAMIS item), the file is still written. That amount goes to `3001 Revenue` with **CHECK** at the start of the description, and the window prints a CHECK flag. Fix that one line in QuickBooks after import.

To make a new account permanent, double-click **ADD ACCOUNT** and answer the three questions. (It writes `extra_accounts.json`, which looks like this:)

    {"4550": {"qbo": "3022 Revenue - Firewood", "prefix": "Firewood"}}

The `qbo` name must match the QuickBooks Chart of Accounts exactly.

It only refuses to write a file when the numbers themselves are wrong: the two reports disagree, the Trial Balance does not balance, or the entry does not balance.

If Claude fixes something, double-click **UPDATE** to get the new version. Your PDFs, journal number and saved accounts are untouched.

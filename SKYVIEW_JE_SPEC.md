# Skyview Daily Revenue JE Builder — Build Spec (credit-optimized)

Builds a QuickBooks Online journal-entry CSV from two daily Skyview
Campground PDFs (GL Summary Report + Trial Balance). Owner: Imran,
Accounting Administrator, Manning Park Resort.

## 0. Credit rules — read first

Claude Code credits are spent on tokens. The way to spend almost none is
to make the daily run **a plain Python script that needs no AI at all**.
Claude is used once to build the script, and afterwards only when the
script stops with a question it cannot answer.

Hard rules for the build:

1. **Deterministic parsing, no LLM.** Extract PDF text with `pdfplumber`
   and parse with regex. Never send PDF contents to Claude to "read".
   One day's PDFs read by a model costs more than a month of script runs.
2. **Daily run is `python skyview_je.py <gl.pdf> <tb.pdf>`.** Zero
   credits. Output: the CSV, a balance summary, and a Flags section.
3. **Claude is only invoked on STOP conditions** (section 6). When that
   happens, paste only the script's STOP message, not the PDFs and not
   this spec. The message must contain everything needed to decide.
4. **Keep this spec out of context on daily runs.** The rules below are
   encoded in the script. A 20-line `CLAUDE.md` pointing at the script
   and the state file is enough for any future Claude session.
5. **Build once, test against known days, then stop iterating.** Ask
   Imran for 2 to 3 already-completed days (PDFs + the CSV he built by
   hand). The script must match them byte-for-byte. Do not spend sessions
   polishing beyond that.
6. **One session for the build.** Plan first, write the whole script,
   run the tests, commit. Avoid many small round-trips; each one re-reads
   context.

Do not guess on accounting questions. A wrong line in the books costs far
more than a clarifying question. But "ask" means the script prints a STOP
message and exits nonzero; it does not mean a Claude conversation.

## 1. Inputs

Two PDFs for the same calendar day:

- **GL Summary Report**: per GL account, each line-item description with
  quantity and dollar total, then an account subtotal. Also lists the
  `1060 Bank account` tender breakdown (Cash, Visa, MasterCard, Debit).
- **Trial Balance (TB)**: one row per GL account with Debits, Credits,
  Group Total. **The TB is the sole source of truth for which side each
  account posts on.** Never infer sign from account nature.

Pre-checks (fail = STOP):

- Both PDFs are for the same date.
- TB total Debits == total Credits.
- Every GL Summary account total == TB figure, to the penny.

## 2. Account mapping (permanent)

| GL account | QBO AccountName | Description prefix |
|---|---|---|
| 1060 Bank account | split by tender, see section 3 | per tender |
| 2200 Deposit Liability | `2009 Deferred Revenue` | none |
| 2250 Security Deposit | `2003 Advance Deposits - Parks` | none; never merge with 2009 |
| 2300 GST | `2029 GST Charged on Sales` | none (bare memo) |
| 2400 PST | `2035 PST 7% Charged on Sales` | none (bare memo) |
| 4140 Camping Revenue | `3033 Camping` | `Camping -` |
| 4145 Out of Province Fee | `3001 Revenue` | `Out of Province Fee -` |
| 4147 Second Vehicle | `3001 Revenue` | `Second Vehicle -` |
| 4155 Snacks | `3014 Revenue - Snacks` | `Snacks -` |
| 4157 Drinks | `3006 Revenue - Non-Alcoholic` | `Drinks -` |
| 4160 Ice Cream | `3007 Revenue - Miscellaneous` | `Ice Cream -` |
| 4165 Ice | `3020 Revenue - Ice` | `Ice -` |
| 4180 Retail | `3021 Revenue - Miscellaneous Retail` | `Retail -` |
| 4200 WiFi Revenue | `3001 Revenue` | `Wifi -` |
| 4220 Rentals | `3001 Revenue` | `Rentals -` |
| 4225 Propane | `3001 Revenue` | `Propane -` |
| 4300 Cancellation Fees | `3001 Revenue` | `Cancellation Fees -` |
| 4400 Reservation Fee | `3001 Revenue` | `Reservation Fee -` |
| 4500 Hydro Revenue | `6007 Utilities (DS)` | `BC Hydro -` (confirmed; expense-side, not 3xxx) |

- Any GL account not in this table → STOP. Never bucket into 3001.
- Multiple categories mapping to 3001 post as **separate lines**, each
  with its own prefix. Never combine.
- Store this table in the script as a single dict so it is the only
  place to edit when a new account is confirmed.

## 3. Tenders (1060 breakdown)

- Cash → `1002 Petty Cash in safe`, prefix `Cash -`.
- Visa, MasterCard, Debit Card → `1007 Visa / Mstrcrd / Debit Receivable`,
  **one line per card type**, prefixes `Visa -`, `MasterCard -`,
  `Debit card -`.
- Only tenders present and non-zero get a line.
- Sign is per tender, read from the GL Summary figure. Parentheses =
  negative = credit = net refund. Several tenders negative on the same
  day is normal (wildfire cancellations, Aug 2026). Never "correct" it.
- Net-negative tender: description `Visa (net refund) - {Memo}`.
- Check: Cash line + all card lines, signed, == TB `1060` Group Total to
  the penny. Mismatch → STOP.

## 4. Sign rules

The TB column decides every sign, every day. Specifically:

1. **2200 → 2009**: flips unpredictably (16 days debit, then credit,
   then back). Post on whichever side the TB shows.
2. **2250 → 2003**: "Rental Deposit" collections credit, "Deposit
   Refund" debit. Post the single **net** TB figure on the TB side. Net
   $0.00 → omit. Never combine with 2009.
3. **Revenue categories** normally credit but can go debit (seen for
   Second Vehicle, Cancellation Fees, WiFi). Post as debit, append
   `(net refund)` to the prefix, and flag it.
4. **GST/PST** always credit so far. Still read the TB column.

## 5. Line rules

- **No $0.00 lines, ever.** A category netting to $0.00 is normal; omit
  silently and mention it in Flags.
- **CAMIS class split**: a Camping sub-item exactly matching
  `LL Additional Party/3rd V` (GL 4130 in some data) posts to
  `3033 Camping` with Class `0050-MANNING PARKS`. Everything else uses
  `0052-SKYVIEW`. A near-match that is not exact → STOP.
- **Memo** on every row: `Skyview Daily Revenue DD Month YYYY` (no comma).
- **Description**: `{prefix} {Memo}` per table, or bare Memo for GST/PST.
  No commas anywhere in a Description.

## 6. STOP conditions

The script prints `STOP:` plus a self-contained explanation and exits 2.
Never auto-reconcile, plug, round, or guess. Conditions:

- Unmapped GL account (print the account line as seen).
- GL Summary vs TB mismatch on any account (print both figures).
- TB does not balance itself (say so distinctly; usually a missing
  "GL Not Assigned - NA" item on the source report).
- PDFs are for different dates.
- Tender sum != TB 1060 total.
- CAMIS-like description that is not an exact match.
- No journal number available and auto-increment is off.
- Final JE debits != credits (print every line included).

The STOP message is the only thing Imran should need to paste to Claude
if he wants help. It must stand alone.

## 7. CSV output

Header, exact order:

```
*JournalNo,*JournalDate,Memo,*AccountName,Debits,Credits,Description,Name,Location,Class
```

- JournalNo, JournalDate, Memo repeat on every row.
- JournalDate is `DD-MM-YYYY`.
- AccountName strings exactly as in section 2 (spaces around dashes).
- Exactly one of Debits/Credits filled; the other is empty, never `0`.
- Name and Location always empty.
- **CRLF line endings.** Open the file with `newline=""` and pass
  `lineterminator="\r\n"` to `csv.writer`; assert it after writing.
- File name: `JJ####_Skyview_MonDD.csv`.
- Before writing: sum debits and credits; must equal each other and the
  TB total. Otherwise STOP.

## 8. Journal number and state

`skyview_je_state.json` holds `last_journal_no`, `last_date`,
`auto_increment` (default false), and prior-day signs for 2009/2003.

- `--journal NNNN` uses that number. If it is not last+1, use it anyway,
  flag the gap, and make it the new baseline.
- `--auto` sets auto_increment true; later runs use last+1 without
  asking and print the number used.
- No number, auto off → STOP.
- Never invent a number.

## 9. Console output

Every run prints: journal number, date, total debits, total credits,
balanced yes/no, then a **Flags** section (always present, "No anomalies
today" when empty): net-refund lines with amounts, journal gap, omitted
$0.00 categories, sign flips on 2009/2003 vs prior day, and anything
unrecognized printed loudly at the top.

## 10. Fetching the reports automatically

Optional, decide after the builder works. Ranked by effort:

1. **Email or folder watch (cheapest).** If the reports arrive by email
   or land in a shared folder, a watcher that picks up the newest pair
   and runs the script needs no login at all. Half a day of work.
2. **Browser login with Playwright.** Script logs in to the booking
   system, runs both reports for yesterday, downloads the PDFs, then
   runs the builder. About one to two days of work. Needs: the login
   URL, a dedicated read-only account, and either no two-factor auth or
   an app-password/TOTP secret the script can hold. Any redesign of the
   report page breaks it and needs a fix session. Store credentials in
   an OS keychain or `.env` that is never committed.
3. **Vendor API.** Clover has a REST API, but the GL Summary and Trial
   Balance are produced by the booking/reporting system, so confirm
   which system actually generates them and whether it exposes an
   export endpoint. If it does, this is the most robust route and the
   PDF parser can be replaced with a JSON/CSV reader.

Whichever route is used, the builder still runs the same checks and
still STOPs on the same conditions. Auto-fetch never means auto-post
to QBO: Imran still imports the CSV.

## 11. Testing

Reproduce 2 to 3 hand-built days exactly (diff the CSV bytes). Then
freeze the script. Keep the sample PDFs and expected CSVs in `tests/`
so any later change can be re-verified locally at no credit cost.

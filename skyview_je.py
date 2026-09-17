#!/usr/bin/env python3
"""Skyview Campground daily revenue JE builder.

Usage:
    python skyview_je.py GLSummary.pdf TrialBalance.pdf --journal 3528
    python skyview_je.py GLSummary.pdf TrialBalance.pdf --auto
    python skyview_je.py GLSummary.pdf TrialBalance.pdf            # uses --auto if state says so

Turns the two daily PDFs into a QuickBooks Online journal entry CSV.
Needs no AI. On anything it is not sure about it prints "STOP:" and exits 2.
"""
import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime
from decimal import Decimal

import pdfplumber

# ---------------------------------------------------------------- mappings
# The only place to edit when Imran confirms a new account.
# prefix None = bare memo as description.
ACCOUNTS = {
    "2200": ("2009 Deferred Revenue", None),
    "2250": ("2003 Advance Deposits - Parks", None),
    "2300": ("2029 GST Charged on Sales", None),
    "2400": ("2035 PST 7% Charged on Sales", None),
    "4140": ("3033 Camping", "Camping"),
    "4145": ("3001 Revenue", "Out of Province Fee"),
    "4147": ("3001 Revenue", "Second Vehicle"),
    "4155": ("3014 Revenue - Snacks", "Snacks"),
    "4157": ("3006 Revenue - Non-Alcoholic", "Drinks"),
    "4160": ("3007 Revenue - Miscellaneous", "Ice Cream"),
    "4165": ("3020 Revenue - Ice", "Ice"),
    "4180": ("3021 Revenue - Miscellaneous Retail", "Retail"),
    "4200": ("3001 Revenue", "Wifi"),
    "4220": ("3001 Revenue", "Rentals"),
    "4225": ("3001 Revenue", "Propane"),
    "4300": ("3001 Revenue", "Cancellation Fees"),
    "4400": ("3001 Revenue", "Reservation Fee"),
    "4500": ("6007 Utilities (DS)", "BC Hydro"),
}
BANK = "1060"
TENDERS = {  # GL tender name -> (QBO account, description prefix)
    "Cash": ("1002 Petty Cash in safe", "Cash"),
    "Visa": ("1007 Visa / Mstrcrd / Debit Receivable", "Visa"),
    "MasterCard": ("1007 Visa / Mstrcrd / Debit Receivable", "MasterCard"),
    "Debit Card": ("1007 Visa / Mstrcrd / Debit Receivable", "Debit card"),
}
TENDER_ORDER = ["Cash", "Visa", "MasterCard", "Debit Card"]
CAMIS_DESC = "LL Additional Party/3rd V"
CAMIS_ACCOUNT = "4130"
CLASS_DEFAULT = "0052-SKYVIEW"
CLASS_CAMIS = "0050-MANNING PARKS"
STATE_FILE = "skyview_je_state.json"
HEADER = ["*JournalNo", "*JournalDate", "Memo", "*AccountName", "Debits",
          "Credits", "Description", "Name", "Location", "Class"]


class Stop(Exception):
    pass


def money(s):
    """'$1,407.57' -> 1407.57 ; '($396.00)' -> -396.00 ; '-' -> None."""
    s = s.strip()
    if s in ("-", ""):
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()").replace("$", "").replace(",", "")
    v = Decimal(s)
    return -v if neg else v


def pdf_text(path):
    with pdfplumber.open(path) as pdf:
        return "\n".join(p.extract_text() or "" for p in pdf.pages)


# ------------------------------------------------------------------ parsing
DATE_RE = re.compile(r"For:\s*(\d{1,2} \w{3}, \d{4}) to (\d{1,2} \w{3}, \d{4})")


def parse_date(text, label):
    m = DATE_RE.search(text)
    if not m:
        raise Stop(f"{label}: could not find the report date line.")
    if m.group(1) != m.group(2):
        raise Stop(f"{label}: report covers {m.group(1)} to {m.group(2)}, not a single day.")
    return datetime.strptime(m.group(1), "%d %b, %Y").date()


def parse_gl_summary(text):
    """Returns (date, {acct: {'name', 'items': [(desc, qty, amt)], 'total'}})."""
    date = parse_date(text, "GL Summary")
    accounts, cur = {}, None
    hdr = re.compile(r"^(\d{4}) - (.+)$")
    item = re.compile(r"^(.*?) Quantity: (\d+) (\(?\$[\d,]+\.\d{2}\)?)$")
    total = re.compile(r"^Total Quantity: \d+ (\d{4}) - - .+ Total: (\(?\$[\d,]+\.\d{2}\)?)$")
    for line in text.splitlines():
        line = line.strip()
        m = total.match(line)
        if m:
            accounts[m.group(1)]["total"] = money(m.group(2))
            cur = None
            continue
        m = hdr.match(line)
        if m:
            cur = m.group(1)
            accounts[cur] = {"name": m.group(2).strip(), "items": [], "total": None}
            continue
        m = item.match(line)
        if m and cur:
            accounts[cur]["items"].append((m.group(1).strip(), int(m.group(2)), money(m.group(3))))
    for a, d in accounts.items():
        if d["total"] is None:
            raise Stop(f"GL Summary: account {a} has no Total line.")
        s = sum(x[2] for x in d["items"])
        if s != d["total"]:
            raise Stop(f"GL Summary: items in {a} sum to {s} but Total says {d['total']}.")
    return date, accounts


def parse_trial_balance(text):
    """Returns (date, {acct: {'name','debit','credit','group'}}, (tot_dr, tot_cr))."""
    date = parse_date(text, "Trial Balance")
    row = re.compile(r"^(.+?) (\d{4}) (\(?\$[\d,]+\.\d{2}\)?|-) (\(?\$[\d,]+\.\d{2}\)?|-) (\(?\$[\d,]+\.\d{2}\)?)$")
    tot = re.compile(r"^Trial Balance Total: (\$[\d,]+\.\d{2}) (\$[\d,]+\.\d{2})$")
    rows, totals = {}, None
    for line in text.splitlines():
        line = line.strip()
        m = row.match(line)
        if m:
            rows[m.group(2)] = {"name": m.group(1), "debit": money(m.group(3)),
                                "credit": money(m.group(4)), "group": money(m.group(5))}
            continue
        m = tot.match(line)
        if m:
            totals = (money(m.group(1)), money(m.group(2)))
    if totals is None:
        raise Stop("Trial Balance: could not find the 'Trial Balance Total' line.")
    for a, r in rows.items():
        if (r["debit"] is None) == (r["credit"] is None):
            raise Stop(f"Trial Balance: account {a} has both or neither of Debits/Credits filled. Cannot read its side.")
    return date, rows, totals


# ------------------------------------------------------------------- checks
def cross_check(gl_date, gl, tb_date, tb, tb_totals):
    if gl_date != tb_date:
        raise Stop(f"GL Summary is for {gl_date} but Trial Balance is for {tb_date}.")
    if tb_totals[0] != tb_totals[1]:
        raise Stop("Trial Balance does not balance against itself: "
                   f"Debits {tb_totals[0]} vs Credits {tb_totals[1]}. This points at the "
                   "source report (often a missing 'GL Not Assigned - NA' item), not at this script.")
    dr = sum(r["debit"] for r in tb.values() if r["debit"] is not None)
    cr = sum(r["credit"] for r in tb.values() if r["credit"] is not None)
    if dr != tb_totals[0] or cr != tb_totals[1]:
        raise Stop(f"Trial Balance rows sum to Dr {dr} / Cr {cr} but its stated total is "
                   f"{tb_totals[0]} / {tb_totals[1]}. A row was probably not parsed.")
    problems = []
    for a in sorted(set(gl) | set(tb)):
        if a not in gl:
            problems.append(f"account {a} is on the Trial Balance but not in the GL Summary")
        elif a not in tb:
            problems.append(f"account {a} is in the GL Summary but not on the Trial Balance")
        elif abs(gl[a]["total"]) != abs(tb[a]["group"]):
            # GL Summary signs follow each account's own convention; only magnitudes are compared.
            # The Trial Balance column is the only source for debit/credit.
            problems.append(f"account {a}: GL Summary total {gl[a]['total']} vs Trial Balance {tb[a]['group']}")
    if problems:
        raise Stop("GL Summary and Trial Balance do not agree:\n  - " + "\n  - ".join(problems))
    unmapped = [f"{a} - {gl[a]['name']}" for a in gl
                if a not in ACCOUNTS and a not in (BANK, CAMIS_ACCOUNT)]
    if unmapped:
        raise Stop("Unmapped GL account(s), ask Imran which QBO account they map to:\n  - "
                   + "\n  - ".join(unmapped))


# ------------------------------------------------------------------- build
def side_of(tb_row):
    """Returns ('debit', amount) or ('credit', amount) from the TB row."""
    if tb_row["debit"] is not None:
        return "debit", tb_row["debit"]
    return "credit", tb_row["credit"]


def build_lines(gl, tb, memo, flags):
    """Returns list of dicts: account, side, amount, desc, cls."""
    lines = []

    def add(account, side, amount, prefix, cls=CLASS_DEFAULT, net_refund=False):
        if amount == 0:
            return
        if prefix is None:
            desc = memo
        else:
            desc = f"{prefix}{' (net refund)' if net_refund else ''} - {memo}"
        if "," in desc:
            raise Stop(f"Description would contain a comma: {desc!r}")
        lines.append({"account": account, "side": side, "amount": amount, "desc": desc, "cls": cls})

    # Tenders. GL Summary sign: positive = net debit, parentheses = net credit.
    if BANK in gl:
        seen = {d: amt for d, _, amt in gl[BANK]["items"]}
        unknown = [d for d in seen if d not in TENDERS]
        if unknown:
            raise Stop(f"Unknown tender type(s) under 1060: {unknown}")
        net = Decimal(0)
        for t in TENDER_ORDER:
            amt = seen.get(t)
            if amt is None or amt == 0:
                continue
            net += amt
            acct, prefix = TENDERS[t]
            if amt > 0:
                add(acct, "debit", amt, prefix)
            else:
                add(acct, "credit", -amt, prefix, net_refund=True)
                flags.append(f"NET REFUND tender: {t} {amt}")
        if net != tb[BANK]["group"]:
            raise Stop(f"Tender lines net to {net} but Trial Balance 1060 total is {tb[BANK]['group']}.")

    # CAMIS class-split checks.
    camis_amount = Decimal(0)
    for a in gl:
        for desc, _, amt in gl[a]["items"]:
            if desc == CAMIS_DESC and a in (CAMIS_ACCOUNT, "4140"):
                camis_amount += amt
            elif desc == CAMIS_DESC or (a == CAMIS_ACCOUNT) or \
                    ("additional party" in desc.lower() or "3rd v" in desc.lower()):
                raise Stop(f"Item '{desc}' under account {a} looks like the CAMIS class-split "
                           f"case but is not an exact match to '{CAMIS_DESC}' under 4130/4140. Ask Imran.")

    # Every other account, side straight from the TB.
    for a in [x for x in tb if x != BANK]:
        if a == CAMIS_ACCOUNT:
            side, amt = side_of(tb[a])
            add("3033 Camping", side, amt, "Camping", cls=CLASS_CAMIS)
            continue
        qbo, prefix = ACCOUNTS[a]
        side, amt = side_of(tb[a])
        if a == "4140" and camis_amount:
            # split the CAMIS sub-item out of the Camping total
            # Both parts take the TB side; magnitude of the CAMIS item comes from the GL Summary.
            camis = abs(camis_amount)
            rest = amt - camis
            if rest < 0:
                raise Stop(f"CAMIS item {camis} exceeds the Camping total {amt}. Ask Imran.")
            add(qbo, side, rest, prefix, net_refund=(side == "debit"))
            add(qbo, side, camis, prefix, cls=CLASS_CAMIS, net_refund=(side == "debit"))
            flags.append(f"CAMIS split: {camis_amount} of Camping posted to class {CLASS_CAMIS}")
            continue
        if amt == 0:
            flags.append(f"Zero-dollar category omitted: {a} {gl[a]['name']}")
            continue
        is_rev = a.startswith("4")
        nr = is_rev and side == "debit"
        if nr:
            flags.append(f"NET REFUND revenue category: {a} {gl[a]['name']} debit {amt}")
        add(qbo, side, amt, prefix, net_refund=nr)
    # zero-dollar accounts that are in the GL but dropped from the TB
    for a in gl:
        if a not in tb and a != BANK and gl[a]["total"] == 0:
            flags.append(f"Zero-dollar category omitted: {a} {gl[a]['name']}")
    return lines


def balance(lines, tb_total):
    dr = sum(l["amount"] for l in lines if l["side"] == "debit")
    cr = sum(l["amount"] for l in lines if l["side"] == "credit")
    if dr != cr or dr != tb_total:
        detail = "\n".join(f"  {l['side']:6} {l['amount']:>10}  {l['account']}  {l['desc']}" for l in lines)
        raise Stop(f"JE does not balance. Debits {dr}, Credits {cr}, Trial Balance total {tb_total}.\n"
                   f"Lines included:\n{detail}")
    return dr, cr


def write_csv(path, lines, journal_no, date, memo):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\r\n")
        w.writerow(HEADER)
        for l in lines:
            w.writerow([journal_no, date.strftime("%d-%m-%Y"), memo, l["account"],
                        f"{l['amount']:.2f}" if l["side"] == "debit" else "",
                        f"{l['amount']:.2f}" if l["side"] == "credit" else "",
                        l["desc"], "", "", l["cls"]])
    with open(path, "rb") as f:
        data = f.read()
    assert b"\r\n" in data and b"\n" not in data.replace(b"\r\n", b""), "CSV is not CRLF"


# -------------------------------------------------------------------- state
def load_state(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"last_journal_no": None, "last_date": None, "auto_increment": False, "last_sides": {}}


def save_state(path, state):
    with open(path, "w") as f:
        json.dump(state, f, indent=2)


def pick_journal(args, state, flags):
    last = state.get("last_journal_no")
    if args.journal is not None:
        n = args.journal
        if last is not None and n != last + 1:
            flags.append(f"Journal number gap: last used JJ{last}, this entry uses JJ{n} (explicit). "
                         f"JJ{n} is the new baseline.")
        return n
    if args.auto or state.get("auto_increment"):
        if last is None:
            raise Stop("Auto-increment is on but no previous journal number is recorded. "
                       "Run once with --journal NNNN.")
        return last + 1
    raise Stop("No journal number given. Use --journal NNNN, or --auto to keep incrementing "
               "from the last one used.")


# --------------------------------------------------------------------- main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("gl_pdf")
    ap.add_argument("tb_pdf")
    ap.add_argument("--journal", type=int, help="journal number, digits only (e.g. 3528)")
    ap.add_argument("--auto", action="store_true", help="turn on auto-increment from now on")
    ap.add_argument("--out-dir", default=".")
    ap.add_argument("--state", default=STATE_FILE)
    args = ap.parse_args(argv)

    flags = []
    try:
        gl_date, gl = parse_gl_summary(pdf_text(args.gl_pdf))
        tb_date, tb, tb_totals = parse_trial_balance(pdf_text(args.tb_pdf))
        cross_check(gl_date, gl, tb_date, tb, tb_totals)
        date = tb_date
        memo = f"Skyview Daily Revenue {date.strftime('%d %B %Y')}"

        state = load_state(args.state)
        journal_no = pick_journal(args, state, flags)

        lines = build_lines(gl, tb, memo, flags)
        for a, key in (("2200", "2009"), ("2250", "2003")):
            if a in tb:
                side, _ = side_of(tb[a])
                prev = state.get("last_sides", {}).get(key)
                if prev and prev != side:
                    flags.append(f"Sign flip on {key}: was {prev} on {state.get('last_date')}, is {side} today")
                state.setdefault("last_sides", {})[key] = side
        dr, cr = balance(lines, tb_totals[0])

        out = os.path.join(args.out_dir, f"JJ{journal_no}_Skyview_{date.strftime('%b%d')}.csv")
        write_csv(out, lines, journal_no, date, memo)
    except Stop as e:
        print(f"STOP: {e}")
        print("Nothing was written. Fix the input or ask Imran, then rerun.")
        return 2

    state.update({"last_journal_no": journal_no, "last_date": str(date),
                  "auto_increment": bool(args.auto or state.get("auto_increment"))})
    save_state(args.state, state)

    print(f"Wrote {out}")
    print(f"Journal JJ{journal_no}  Date {date.strftime('%d-%m-%Y')}  Lines {len(lines)}")
    print(f"Debits {dr:.2f}  Credits {cr:.2f}  Balanced: YES (matches Trial Balance total)")
    print("\nFlags / Things to look out for:")
    loud = [f for f in flags if f.startswith(("NET REFUND", "Journal number gap", "Sign flip", "CAMIS"))]
    quiet = [f for f in flags if f not in loud]
    for f in loud + quiet:
        print(f"  - {f}")
    if not flags:
        print("  No anomalies today")
    return 0


if __name__ == "__main__":
    sys.exit(main())

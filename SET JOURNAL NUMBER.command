#!/bin/bash
cd "$(dirname "$0")"
read -p "Type the journal number to use for the NEXT entry (digits only): " n
python3 -c "import json,os,sys;n=int(sys.argv[1]);p='skyview_je_state.json';s=json.load(open(p)) if os.path.exists(p) else {};s.update(last_journal_no=n-1,auto_increment=True);json.dump(s,open(p,'w'),indent=2);print('OK. Next entry will be JJ%d'%n)" "$n"
read -p "Press Enter to close"

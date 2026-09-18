#!/bin/bash
cd "$(dirname "$0")"
read -p "GL number from the report (e.g. 4550): " gl
read -p "QuickBooks account EXACTLY as in the Chart of Accounts: " qbo
read -p "Description prefix (e.g. Firewood): " prefix
python3 -c "import json,os,sys;g,q,p=sys.argv[1:4];f='extra_accounts.json';d=json.load(open(f)) if os.path.exists(f) else {};d[g]={'qbo':q,'prefix':p};json.dump(d,open(f,'w'),indent=2);print('Saved: %s -> %s (prefix %s)'%(g,q,p))" "$gl" "$qbo" "$prefix"
read -p "Press Enter to close"

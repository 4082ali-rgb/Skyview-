@echo off
cd /d "%~dp0"
echo Add a permanent account mapping.
set /p gl=GL number from the report (e.g. 4550): 
set /p qbo=QuickBooks account EXACTLY as in the Chart of Accounts (e.g. 3022 Revenue - Firewood): 
set /p prefix=Description prefix (e.g. Firewood): 
python -c "import json,os,sys;g,q,p=sys.argv[1:4];f='extra_accounts.json';d=json.load(open(f)) if os.path.exists(f) else {};d[g]={'qbo':q,'prefix':p};json.dump(d,open(f,'w'),indent=2);print('Saved: %%s -> %%s (prefix %%s)'%%(g,q,p))" "%gl%" "%qbo%" "%prefix%"
echo.
pause

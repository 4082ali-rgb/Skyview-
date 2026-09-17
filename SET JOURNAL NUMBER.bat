@echo off
cd /d "%~dp0"
set /p n=Type the journal number to use for the NEXT entry (digits only): 
python -c "import json,sys;n=int(sys.argv[1]);p='skyview_je_state.json';s=json.load(open(p)) if __import__('os').path.exists(p) else {};s.update(last_journal_no=n-1,auto_increment=True);json.dump(s,open(p,'w'),indent=2);print('OK. Next entry will be JJ%%d'%%n)" %n%
echo.
pause

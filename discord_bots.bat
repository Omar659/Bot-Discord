@echo off
REM %~dp0 e' la cartella di questo file: cosi' funziona anche da un
REM collegamento sul desktop, qualunque sia la cartella di avvio
cd /d "%~dp0"
start /B pythonw "%~dp0main.py"

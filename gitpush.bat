@echo off
echo [SEKTOR 7] SYSTEM UPLINK INITIATED...

:: 1. Alle Änderungen erfassen
git add .

:: 2. Commit mit automatischem Zeitstempel erstellen
git commit -m "Sektor 7 Auto-Update: %date% - %time%"

:: 3. Zum Server senden
git push

echo.
echo [SEKTOR 7] OPERATION COMPLETE.
pause
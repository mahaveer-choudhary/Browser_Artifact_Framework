@echo off
echo [*] Cleaning up background processes...
taskkill /F /IM chrome.exe /IM msedge.exe /IM brave.exe /IM firefox.exe /IM python.exe /IM opera.exe /IM vivaldi.exe 2>nul
timeout /t 2 /nobreak >nul

echo.
echo [*] Extracting Chrome Secrets...
python main.py /b:chrome /f:secrets_chrome.json

echo.
echo [*] Extracting Edge Secrets...
python main.py /b:edge /f:secrets_edge.json

echo.
echo [*] Extracting Firefox Secrets...
python main.py /b:firefox /f:secrets_firefox.json

echo.
echo [*] Extracting Brave Secrets...
python main.py /b:brave /f:secrets_brave.json

echo.
echo [+] All Done. Check the json files.
pause

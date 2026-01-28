@echo off
:: Check if the server is already running, if not, start it
start /b python app.py
timeout /t 3 /nobreak > nul
:: Open the interface
start http://127.0.0.1:5000
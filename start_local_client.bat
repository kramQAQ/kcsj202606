@echo off
setlocal
cd /d %~dp0

start "Yinpian Inference Server" cmd /k ".\.venv\python.exe .\main.py --host 127.0.0.1 --port 8868"
timeout /t 8 /nobreak > nul
.\.venv\python.exe .\desktop_client.py

@echo off
cd /d "%~dp0"
python -m uvicorn main:app --host localhost --port 8000

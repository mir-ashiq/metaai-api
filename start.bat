@echo off
echo ======================================================================
echo Meta AI API Server
echo ======================================================================
echo.
echo Starting server...
echo Server: http://127.0.0.1:8000
echo Docs:   http://127.0.0.1:8000/docs
echo Health: http://127.0.0.1:8000/health
echo.
echo Press Ctrl+C to stop
echo ======================================================================
echo.

cd /d "%~dp0"
set PYTHONPATH=%CD%\src
.venv\Scripts\hypercorn.exe server:app --bind 127.0.0.1:8000

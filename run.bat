@echo off
title Resume & Cover Letter Generator
echo Starting Resume & Cover Letter Generator...
echo.

cd /d "%~dp0"

:: Check for .env file
if not exist .env (
    echo WARNING: .env file not found. Copy .env.example to .env and add your DEEPSEEK_API_KEY.
    echo.
)

:: Kill leftover Word processes from previous runs
taskkill /F /IM WINWORD.EXE >nul 2>&1

:: Activate venv and launch
call .venv\Scripts\activate.bat
start http://localhost:8501
streamlit run app.py --server.port 8501 --server.headless true

pause

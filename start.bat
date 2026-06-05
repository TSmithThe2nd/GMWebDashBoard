@echo off
title Thekodia DM Dashboard
echo.
echo  ==========================================
echo    Thekodia DM Dashboard
echo    Starting server at http://localhost:5000
echo  ==========================================
echo.

cd /d "%~dp0"

REM Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10 or later.
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Checking dependencies...
pip install flask pypdf pdfplumber pywebview --quiet

echo Starting server...
python app.py

pause

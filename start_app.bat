@echo off
title Thekodia DM Dashboard
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.10 or later.
    pause
    exit /b 1
)

echo Checking dependencies...
pip install flask pypdf pdfplumber pywebview --quiet

echo Launching Thekodia...
python app_webview.py
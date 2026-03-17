@echo off
REM YouTube Audio Player - Windows Launcher

echo 🎵 YouTube Audio Player
echo =======================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed
    echo Please install Python from python.org
    exit /b 1
)

REM Check if venv exists, if not create it
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate venv
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo 📥 Checking dependencies...
pip install -q -r requirements.txt

REM Run the application
echo 🚀 Starting YouTube Audio Player...
cd src
python main.py
pause

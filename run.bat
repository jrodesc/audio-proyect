@echo off
setlocal
cd /d "%~dp0"

echo YouTube Audio Player - Windows
echo =============================

where python >nul 2>&1
if errorlevel 1 goto no_python

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if errorlevel 1 goto old_python

set "VENV_PYTHON=%~dp0venv\Scripts\python.exe"
if not exist "%VENV_PYTHON%" goto create_venv
"%VENV_PYTHON%" -m pip --version >nul 2>&1
if errorlevel 1 goto create_venv
goto install_dependencies

:create_venv
echo Creating or repairing virtual environment...
python -m venv --clear "%~dp0venv"
if errorlevel 1 goto venv_error

:install_dependencies
echo Installing/checking Python dependencies...
"%VENV_PYTHON%" -m pip install -q -r "%~dp0requirements.txt"
if errorlevel 1 goto dependency_error

where mpv >nul 2>&1
if not errorlevel 1 goto launch_app
if exist "%ProgramFiles%\mpv\mpv.exe" goto launch_app
if exist "%ProgramFiles(x86)%\mpv\mpv.exe" goto launch_app
if exist "C:\mpv\mpv.exe" goto launch_app
if exist "%USERPROFILE%\scoop\apps\mpv\current\mpv.exe" goto launch_app
if exist "%USERPROFILE%\scoop\apps\mpv\current\bin\mpv.exe" goto launch_app
if exist "%USERPROFILE%\scoop\shims\mpv.exe" goto launch_app
echo.
echo Warning: mpv is not installed or was not found.
echo Audio playback requires mpv and its libmpv DLLs.
echo Install it with Scoop: scoop install mpv
echo Or install a Windows build from https://mpv.io/installation/ and restart this script.
echo.

:launch_app
echo Starting application...
cd /d "%~dp0src"
"%VENV_PYTHON%" main.py
if errorlevel 1 goto app_error
exit /b 0

:no_python
echo Error: Python 3 is not installed or is not available as "python" in PATH.
echo Install Python 3.10 or newer from https://www.python.org/downloads/windows/
echo During setup, enable "Add python.exe to PATH".
goto failed

:old_python
echo Error: Python could not run or Python 3.10 or newer is required by the current dependencies.
goto failed

:venv_error
echo Error: Could not create the virtual environment.
echo Repair or reinstall Python, then try again.
goto failed

:dependency_error
echo Error: Could not install dependencies. Check the internet connection and try again.
goto failed

:app_error
echo The application exited with an error.
goto failed

:failed
echo.
pause
exit /b 1

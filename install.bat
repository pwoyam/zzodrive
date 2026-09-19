@echo off
REM zzoDrive installer for Windows

cd /d "%~dp0"

echo.
echo ============================================================
echo         zzoDrive installer
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo ERROR: python not found.
    echo Install it from https://www.python.org/downloads/
    pause
    exit /b 1
)

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat

echo Installing dependencies...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt

echo.
echo ============================================================
echo   Installation complete!
echo ============================================================
echo.
echo   To start zzoDrive:
echo.
echo       start.bat
echo.
pause

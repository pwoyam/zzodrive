@echo off
cd /d "%~dp0"

if not exist ".venv" (
    echo First run - installing dependencies...
    call install.bat
)

call .venv\Scripts\activate.bat
python run.py
pause

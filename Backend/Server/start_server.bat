@echo off
setlocal

if not exist "..\.venv\Scripts\python.exe" (
    echo Backend virtual environment not found.
    echo Create it with: py -m venv Backend\.venv
    echo Then install dependencies with: Backend\.venv\Scripts\python.exe -m pip install -r Backend\requirements.txt
    exit /b 1
)

"..\.venv\Scripts\python.exe" "%~dp0start_server.py"

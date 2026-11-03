@echo off
rem SlidePDF Studio - Windows Launcher
setlocal

cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    set "PYTHON_EXEC=.venv\Scripts\pythonw.exe"
    set "PYTHON_CLI=.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXEC=pythonw.exe"
    set "PYTHON_CLI=python.exe"
)

set "PYTHONPATH=%~dp0src;%PYTHONPATH%"

if "%~1"=="" (
    start "" "%PYTHON_EXEC%" -m slidepdf.app
) else (
    "%PYTHON_CLI%" -m slidepdf.cli %*
)

endlocal

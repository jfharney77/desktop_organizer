@echo off
setlocal

REM install_vision_pip.bat
REM Install Python dependencies (pip) and pull the llama3.2-vision Ollama model.

REM Navigate to project root (2 levels up from script\bat\)
pushd %~dp0..\..\..
echo Project root: %CD%

REM --- Python dependencies ---
if not exist ".pipvenv" (
    echo Creating virtual environment in .pipvenv ...
    python -m venv .pipvenv

    echo Upgrading pip ...
    .pipvenv\Scripts\pip install --upgrade pip

    echo Installing dependencies from requirements.txt ...
    .pipvenv\Scripts\pip install -r requirements.txt
) else (
    echo .pipvenv already exists -- skipping Python install.
)

REM --- Ollama model ---
where ollama >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Error: ollama is not installed or not on PATH.
    echo Install it from https://ollama.com and re-run this script.
    popd
    exit /b 1
)

echo.
echo Pulling llama3.2-vision model (this may take a while on first run) ...
ollama pull llama3.2-vision

echo.
echo Done!  Run the vision service with: script\bat\run_vision_pip.bat

popd
endlocal

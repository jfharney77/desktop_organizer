@echo off
setlocal

REM install_vision_uv.bat
REM Install Python dependencies (uv) and pull the llama3.2-vision Ollama model.

REM Navigate to project root (2 levels up from script\bat\)
pushd %~dp0..\..
echo Project root: %CD%

REM --- uv ---
where uv >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo uv not found -- installing via PowerShell...
    powershell -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    echo.
    echo uv has been installed. You may need to restart your terminal for PATH changes
    echo to take effect, then re-run this script.
    popd
    exit /b 0
)

echo uv version:
uv --version

REM --- Python dependencies ---
if not exist ".venv" (
    echo Creating virtual environment in .venv ...
    uv venv .venv

    echo Installing dependencies from requirements.txt ...
    uv pip install --link-mode=copy -r requirements.txt
) else (
    echo .venv already exists -- skipping Python install.
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
echo Done!  Run the vision service with: script\bat\run_vision_uv.bat

popd
endlocal

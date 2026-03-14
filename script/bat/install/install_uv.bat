@echo off
setlocal

REM install_uv.bat
REM Create a uv-managed virtual environment (.venv) and install all dependencies.

REM Navigate to project root (2 levels up from script\bat\)
pushd %~dp0..\..\..
echo Project root: %CD%

REM Check if uv is available
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

echo Creating virtual environment in .venv ...
uv venv .venv

echo Installing dependencies from requirements.txt ...
uv pip install --link-mode=copy -r requirements.txt

echo.
echo Done!  To activate manually: .venv\Scripts\activate

popd
endlocal

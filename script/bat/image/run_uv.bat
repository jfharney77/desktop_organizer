@echo off
setlocal

REM run_uv.bat
REM Start the FastAPI server using the uv-managed .venv environment.

REM Navigate to project root (2 levels up from script\bat\)
pushd %~dp0..\..\..
echo Project root: %CD%

if not exist ".venv" (
    echo Error: .venv not found. Run install_uv.bat first.
    popd
    exit /b 1
)

echo Starting FastAPI server on http://0.0.0.0:8000 ...
uv run uvicorn api:app --app-dir src --host 0.0.0.0 --port 8000 --reload

popd
endlocal

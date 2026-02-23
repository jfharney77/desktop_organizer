@echo off
setlocal

REM run_vision_uv.bat
REM Start the vision FastAPI service on port 8001 using the uv-managed .venv environment.

REM Navigate to project root (2 levels up from script\bat\)
pushd %~dp0..\..
echo Project root: %CD%

if not exist ".venv" (
    echo Error: .venv not found. Run install_vision_uv.bat first.
    popd
    exit /b 1
)

echo Starting vision FastAPI service on http://0.0.0.0:8001 ...
echo Endpoint: POST http://localhost:8001/describe
echo.
uv run uvicorn api:app --app-dir src --host 0.0.0.0 --port 8001 --reload

popd
endlocal

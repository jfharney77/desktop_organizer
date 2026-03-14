@echo off
setlocal

REM run_vision_pip.bat
REM Start the vision FastAPI service on port 8001 using the pip-managed .pipvenv environment.

REM Navigate to project root (2 levels up from script\bat\)
pushd %~dp0..\..\..
echo Project root: %CD%

if not exist ".pipvenv" (
    echo Error: .pipvenv not found. Run install_vision_pip.bat first.
    popd
    exit /b 1
)

echo Starting vision FastAPI service on http://0.0.0.0:8001 ...
echo Endpoint: POST http://localhost:8001/describe
echo.
call .pipvenv\Scripts\activate
uvicorn api:app --app-dir src --host 0.0.0.0 --port 8001 --reload

popd
endlocal

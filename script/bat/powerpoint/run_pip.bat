@echo off
setlocal

REM run_pip.bat  (powerpoint)
REM Start the PowerPoint organizer FastAPI service on port 8002
REM using the pip-managed .pipvenv environment.

REM Navigate to project root (3 levels up from script\bat\powerpoint\)
pushd %~dp0..\..\..
echo Project root: %CD%

if not exist ".pipvenv" (
    echo Error: .pipvenv not found. Run install_pip.bat first.
    popd
    exit /b 1
)

echo Starting PowerPoint organizer FastAPI service on http://0.0.0.0:8002 ...
echo Endpoint: POST http://localhost:8002/organize/powerpoint
echo.
call .pipvenv\Scripts\activate
uvicorn api:app --app-dir src --host 0.0.0.0 --port 8002 --reload

popd
endlocal

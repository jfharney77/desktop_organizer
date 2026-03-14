@echo off
setlocal

REM run_pip.bat
REM Start the FastAPI server using the pip-managed .pipvenv environment.

REM Navigate to project root (2 levels up from script\bat\)
pushd %~dp0..\..\..
echo Project root: %CD%

if not exist ".pipvenv" (
    echo Error: .pipvenv not found. Run install_pip.bat first.
    popd
    exit /b 1
)

echo Starting FastAPI server on http://0.0.0.0:8000 ...
call .pipvenv\Scripts\activate
uvicorn api:app --app-dir src --host 0.0.0.0 --port 8000 --reload

popd
endlocal

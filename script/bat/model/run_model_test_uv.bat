@echo off
setlocal

REM run_model_test_uv.bat
REM Run the model_config.py tester using the uv-managed .venv environment.

REM Navigate to project root (2 levels up from script\bat\)
pushd %~dp0..\..\..
echo Project root: %CD%

if not exist ".venv" (
    echo Error: .venv not found. Run install_uv.bat first.
    popd
    exit /b 1
)

echo Running model_config.py tester ...
echo.
uv run python src\model_config.py

popd
endlocal

@echo off
setlocal

REM run_uv.bat  (notebooks)
REM Launch Jupyter Notebook from the project root using the uv-managed .venv environment.

REM Navigate to project root (3 levels up from script\bat\notebooks\)
pushd %~dp0..\..\..
echo Project root: %CD%

if not exist ".venv" (
    echo Error: .venv not found. Run script\bat\image\install_uv.bat first.
    popd
    exit /b 1
)

echo Starting Jupyter Notebook (notebooks\ directory) ...
echo.
uv run jupyter notebook --notebook-dir=notebooks

popd
endlocal

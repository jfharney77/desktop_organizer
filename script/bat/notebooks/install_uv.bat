@echo off
setlocal

REM install_uv.bat  (notebooks)
REM Install Jupyter into the uv-managed .venv environment.

REM Navigate to project root (3 levels up from script\bat\notebooks\)
pushd %~dp0..\..\..
echo Project root: %CD%

if not exist ".venv" (
    echo Error: .venv not found. Run script\bat\image\install_uv.bat first.
    popd
    exit /b 1
)

echo Installing Jupyter into .venv ...
uv pip install --link-mode=copy notebook

echo.
echo Done!  Launch notebooks with: script\bat\notebooks\run_uv.bat

popd
endlocal

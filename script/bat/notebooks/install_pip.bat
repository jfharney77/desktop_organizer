@echo off
setlocal

REM install_pip.bat  (notebooks)
REM Install Jupyter into the pip-managed .pipvenv environment.

REM Navigate to project root (3 levels up from script\bat\notebooks\)
pushd %~dp0..\..\..
echo Project root: %CD%

if not exist ".pipvenv" (
    echo Error: .pipvenv not found. Run script\bat\image\install_pip.bat first.
    popd
    exit /b 1
)

echo Installing Jupyter into .pipvenv ...
.pipvenv\Scripts\pip install notebook

echo.
echo Done!  Launch notebooks with: script\bat\notebooks\run_pip.bat

popd
endlocal

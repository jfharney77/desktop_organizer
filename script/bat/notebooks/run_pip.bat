@echo off
setlocal

REM run_pip.bat  (notebooks)
REM Launch Jupyter Notebook from the project root using the pip-managed .pipvenv environment.

REM Navigate to project root (3 levels up from script\bat\notebooks\)
pushd %~dp0..\..\..
echo Project root: %CD%

if not exist ".pipvenv" (
    echo Error: .pipvenv not found. Run script\bat\image\install_pip.bat first.
    popd
    exit /b 1
)

echo Starting Jupyter Notebook (notebooks\ directory) ...
echo.
call .pipvenv\Scripts\activate
jupyter notebook --notebook-dir=notebooks

popd
endlocal

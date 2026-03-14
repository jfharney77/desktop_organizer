@echo off
setlocal

REM run_model_test_pip.bat
REM Run the model_config.py tester using the pip-managed .pipvenv environment.

REM Navigate to project root (2 levels up from script\bat\)
pushd %~dp0..\..\..
echo Project root: %CD%

if not exist ".pipvenv" (
    echo Error: .pipvenv not found. Run install_pip.bat first.
    popd
    exit /b 1
)

echo Running model_config.py tester ...
echo.
call .pipvenv\Scripts\activate
python src\model_config.py

popd
endlocal

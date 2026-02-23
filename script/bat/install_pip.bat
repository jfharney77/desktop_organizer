@echo off
setlocal

REM install_pip.bat
REM Create a pip-managed virtual environment (.pipvenv) and install all dependencies.

REM Navigate to project root (2 levels up from script\bat\)
pushd %~dp0..\..
echo Project root: %CD%

echo Creating virtual environment in .pipvenv ...
python -m venv .pipvenv

echo Upgrading pip ...
.pipvenv\Scripts\pip install --upgrade pip

echo Installing dependencies from requirements.txt ...
.pipvenv\Scripts\pip install -r requirements.txt

echo.
echo Done!  To activate manually: .pipvenv\Scripts\activate

popd
endlocal

@echo off
setlocal

REM run_frontend.bat
REM Start the React dev server on http://localhost:3000

pushd %~dp0..\..\..\frontend

if not exist "node_modules" (
    echo Error: node_modules not found. Run 'npm install' in the frontend\ directory first.
    popd
    exit /b 1
)

echo Starting React dev server on http://localhost:3000 ...
npm run dev

popd
endlocal

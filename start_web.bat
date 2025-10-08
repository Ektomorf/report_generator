@echo off
REM Start the Web Frontend Server

echo ============================================================
echo Starting Test Campaign Browser Web Frontend
echo ============================================================
echo.

REM Check if web directory exists
if not exist "web" (
    echo ERROR: Web directory not found!
    exit /b 1
)

echo IMPORTANT: Make sure the API server is running first!
echo.
echo To start the API server, run:
echo   start_api.bat
echo   (or in another terminal: python api_server.py)
echo.
echo Starting web server on http://localhost:8080
echo.
echo Press Ctrl+C to stop
echo ============================================================
echo.

cd web
python -m http.server 8080

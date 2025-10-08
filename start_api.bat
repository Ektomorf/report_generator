@echo off
REM Start the Test Results API Server

echo ============================================================
echo Starting Test Results API Server
echo ============================================================
echo.

REM Check if database exists
if not exist "test_results.db" (
    echo ERROR: Database not found!
    echo.
    echo Please import test results first:
    echo   python sql_importer.py output
    echo.
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
)

echo Starting API server...
echo.
echo Access points:
echo   - API Documentation: http://localhost:8000/docs
echo   - ReDoc:             http://localhost:8000/redoc
echo   - Health Check:      http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

python api_server.py

@echo off
setlocal enabledelayedexpansion
echo ========================================================================
echo                    COMPLETE TEST DATA PROCESSING PIPELINE
echo ========================================================================
echo This will process all test data in the following order:
echo 1. Convert log files to CSV format (flattening JSON data)
echo 2. Combine all test logs into master log across ALL campaigns + per-campaign logs
echo 3. Extract .tar archives in test campaign folders
echo 4. Convert journalctl.log files to CSV format (parsed system logs) [OPTIONAL]
echo 5. Convert JSON result files to CSV format
echo 6. Combine results and logs CSV files by timestamp
echo 7. Generate interactive HTML analyzers for each combined CSV
echo 8. Add test failure information to viewer and analyzer HTML files
echo ========================================================================
echo.

REM Check for --skip-journalctl flag
set SKIP_JOURNALCTL=0
if "%1"=="--skip-journalctl" set SKIP_JOURNALCTL=1
if "%2"=="--skip-journalctl" set SKIP_JOURNALCTL=1
if "%3"=="--skip-journalctl" set SKIP_JOURNALCTL=1

if %SKIP_JOURNALCTL%==1 (
    echo NOTE: Skipping journalctl log processing (--skip-journalctl flag detected)
    echo.
)

set start_time=%time%
echo Started at: %start_time%
echo.

REM Step 1: Convert logs to CSV
echo ========================================================================
echo STEP 1: Converting log files to CSV format...
echo ========================================================================
echo Processing log CSV files and flattening JSON data in message column...
echo.

python process_log_csv.py output/ --pattern "**/*.log" --verbose

if %errorlevel% neq 0 (
    echo ERROR: Log processing failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ✓ Step 1 Complete: CSV files with flattened JSON data created with _logs.csv suffix
echo.

REM Step 1.25: Combine all logs into master log across all campaigns
echo ========================================================================
echo STEP 1.25: Combining all test logs into master log...
echo ========================================================================
echo Creating ALL_CAMPAIGNS_master_log.csv combining all test campaigns...
echo Also creating individual *_all_logs_combined.csv files per campaign...
echo.

python combine_all_logs.py output/ --verbose

if %errorlevel% neq 0 (
    echo ERROR: All logs combination failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ✓ Step 1.25 Complete: Master log and per-campaign logs created
echo.

REM Step 1.5: Extract tar files in test campaign folders
echo ========================================================================
echo STEP 1.5: Extracting .tar archives in test campaign folders...
echo ========================================================================
echo Searching for and extracting .tar files...
echo.

for /r "output\" %%f in (*.tar) do (
    echo Found archive: %%f
    echo Extracting to: %%~dpf
    powershell -Command "tar -xf '%%f' -C '%%~dpf'"
    if !errorlevel! equ 0 (
        echo ✓ Successfully extracted: %%~nxf
    ) else (
        echo ✗ Failed to extract: %%~nxf
    )
    echo.
)

echo ✓ Step 1.5 Complete: All .tar archives extracted
echo.

REM Step 1.75: Convert journalctl logs to CSV (optional)
if %SKIP_JOURNALCTL%==0 (
    echo ========================================================================
    echo STEP 1.75: Converting journalctl.log files to CSV format...
    echo ========================================================================
    echo Converting journalctl.log files to CSV format with parsed timestamp, hostname, program, and message...
    echo Filtering to each campaign's timespan for faster processing...
    echo.

    python process_journalctl_logs.py output/ --batch --verbose

    if !errorlevel! neq 0 (
        echo ERROR: Journalctl log processing failed!
        pause
        exit /b !errorlevel!
    )

    echo.
    echo ✓ Step 1.75 Complete: All journalctl.log files converted to CSV format
    echo.
) else (
    echo ========================================================================
    echo STEP 1.75: Skipping journalctl.log processing (--skip-journalctl)
    echo ========================================================================
    echo.
)

REM Step 2: Convert results to CSV
echo ========================================================================
echo STEP 2: Converting JSON result files to CSV format...
echo ========================================================================
echo Converting all JSON result files to CSV format...
echo.

python process_result_csv.py output/ --pattern "**/*_results.json" --verbose

if %errorlevel% neq 0 (
    echo ERROR: Result processing failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ✓ Step 2 Complete: CSV files created alongside each JSON result file
echo.

REM Step 3: Combine CSV files
echo ========================================================================
echo STEP 3: Combining CSV files from results and logs...
echo ========================================================================
echo Combining CSV files based on timestamp (includes results, logs, and journalctl system logs)...
echo.

python combine_csv_files.py output/ --verbose

if %errorlevel% neq 0 (
    echo ERROR: CSV combination failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ✓ Step 3 Complete: Combined CSV files created with _combined.csv suffix (includes journalctl system logs)
echo.

REM Step 4: Generate HTML analyzers
echo ========================================================================
echo STEP 4: Generating interactive HTML analyzers...
echo ========================================================================
echo Creating HTML analyzers for all combined CSV files...
echo This includes Unix timestamp conversion to readable format (yyyy-mm-dd hh:mm:ss,ms)
echo.

python csv_analyzer.py --batch output/

if %errorlevel% neq 0 (
    echo ERROR: HTML analyzer generation failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ✓ Step 4 Complete: Interactive HTML analyzers generated with _analyzer.html suffix
echo.

REM Step 5: Add failure information to viewer and analyzer HTML files
echo ========================================================================
echo STEP 5: Adding test failure information to viewer and analyzer HTML files...
echo ========================================================================
echo Processing report.json files and updating HTML files with failure details...
echo Removing ANSI escape sequences for clean display...
echo.

python add_failures_to_viewers.py

if %errorlevel% neq 0 (
    echo ERROR: Failure information processing failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ✓ Step 5 Complete: Test failure information added to viewer and analyzer HTML files
echo.

REM Step 6: Generate test campaign browser index
echo ========================================================================
echo STEP 6: Generating test campaign browser index...
echo ========================================================================
echo Creating index.html for browsing test campaigns and failures...
echo.

python generate_index.py

if %errorlevel% neq 0 (
    echo ERROR: Index generation failed!
    pause
    exit /b %errorlevel%
)

echo.
echo ✓ Step 6 Complete: Test campaign browser index.html generated in output/
echo.

REM Calculate processing time
set end_time=%time%
echo ========================================================================
echo                            PROCESSING COMPLETE!
echo ========================================================================
echo Started at:  %start_time%
echo Completed at: %end_time%
echo.
echo Summary of generated files:
echo • Extracted archives         - .tar files extracted to their respective folders
if %SKIP_JOURNALCTL%==0 (
    echo • journalctl_logs.csv        - System logs converted to CSV ^(filtered to campaign timespan^)
)
echo • *_logs.csv                 - Log files converted to CSV with flattened JSON
echo • ALL_CAMPAIGNS_master_log.csv - Master log combining ALL campaigns and tests
echo • *_all_logs_combined.csv    - Per-campaign logs combining all tests in that campaign
echo • *_results.csv              - JSON results converted to CSV
if %SKIP_JOURNALCTL%==0 (
    echo • *_combined.csv        - Results, logs, and journalctl system logs combined by timestamp
) else (
    echo • *_combined.csv        - Results and logs combined by timestamp
)
echo • *_analyzer.html    - Interactive HTML analyzers with Unix timestamp conversion
echo • *_viewer.html      - Enhanced viewer files with test failure information
echo • *_analyzer.html    - Enhanced analyzer files with test failure information
echo • index.html         - Test campaign browser for navigating all test results
echo.
echo Features of HTML analyzers:
echo • Column visibility controls and grouping
echo • Advanced filtering (global + per-column)
echo • Preset management with local storage
echo • Cell expansion for large content
echo • Row highlighting (results vs logs, pass/fail, error levels)
echo • Unix timestamp conversion to readable format
echo • Data export functionality
echo • Responsive design for all devices
echo.
echo Features of enhanced viewer and analyzer HTML files:
echo • Test failure details prominently displayed beneath title
echo • Clean formatting with ANSI escape sequences removed
echo • Professional styling with red background for failed tests
echo • Complete failure traces and error messages
echo.
echo You can now:
echo 1. Open output/index.html to browse all test campaigns and results
echo 2. Open any *_analyzer.html file in your web browser
echo 3. Use the interactive controls to analyze your test data
echo 4. Create custom presets for different analysis workflows
echo 5. Export filtered data as CSV for further analysis
echo 6. View test failure details directly in *_viewer.html and *_analyzer.html files
echo.
echo Options for next run:
echo • Use --skip-journalctl to skip journalctl log processing for faster execution
echo   Example: process_all.bat --skip-journalctl
echo.
echo Happy analyzing! 🚀
echo ========================================================================
pause
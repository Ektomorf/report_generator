@echo off
echo Creating enhanced HTML viewers with integrated CSV data (force mode)...
echo This will regenerate CSV and HTML files even if they already exist.
echo.

echo Step 1: Converting log files to CSV...
python json_to_csv.py output/ --pattern "**/*.log" --verbose

echo.
echo Step 2: Converting results files to CSV...
python json_to_csv.py output/ --pattern "**/*_results.json" --verbose

echo.
echo Step 3: Generating interactive HTML viewers with log and results data (force mode)...
python batch_log_viewer.py output/ --workers 4 --force

echo.
echo Done! Open any *_viewer.html file in your browser to view the interactive log and results data.
echo The HTML viewers now include both log data and results data in separate tabs.
pause
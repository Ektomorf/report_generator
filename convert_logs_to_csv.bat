@echo off
echo Converting all log files to CSV format...
echo.

python json_to_csv.py output/ --pattern "**/*.log" --verbose

echo.
echo Done! CSV files have been created alongside each log file.
echo You can now open the CSV files in Excel or other spreadsheet applications.
pause
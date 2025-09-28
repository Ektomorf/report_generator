@echo off
echo Processing log CSV files and flattening JSON data in message column...
echo.

python process_log_csv.py output/ --pattern "**/*.log" --verbose

echo.
echo Done! CSV files with flattened JSON data have been created with _logs.csv suffix.
echo The JSON keys from the message column are now individual columns.
echo You can now open the CSV files in Excel or other spreadsheet applications.
pause
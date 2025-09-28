@echo off
echo Converting all JSON result files to CSV format...
echo.

python process_result_csv.py output/ --pattern "**/*_results.json" --verbose

echo.
echo Done! CSV files have been created alongside each JSON result file.
echo You can now open the CSV files in Excel or other spreadsheet applications.
pause
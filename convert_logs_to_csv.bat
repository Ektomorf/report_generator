@echo off
echo Processing log files and creating *_logs.csv copies...
echo.

for /r "output" %%f in (*.log) do (
    echo Processing: %%f
    copy "%%f" "%%~dpnf_logs.csv"
)

echo.
echo Done! Log files have been copied with _logs.csv suffix.
echo You can now open the CSV files in Excel or other spreadsheet applications.
pause
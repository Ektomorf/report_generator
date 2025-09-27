@echo off
echo Force processing ALL log files in output/ directory...
echo This will regenerate CSV and HTML files even if they already exist.
echo.

python batch_log_viewer.py output/ --workers 4 --force

echo.
echo Done! Open any *_viewer.html file in your browser to view the interactive log data.
pause
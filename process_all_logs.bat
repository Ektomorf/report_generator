@echo off
echo Processing all log files in output/ directory...
echo.

python batch_log_viewer.py output/ --workers 4

echo.
echo Done! Open any *_viewer.html file in your browser to view the interactive log data.
pause
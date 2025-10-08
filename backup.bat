@echo off
REM Automated backup script for Test Results Archive System (Windows)

setlocal enabledelayedexpansion

REM Configuration
set BACKUP_DIR=backups
set DATABASE_FILE=test_results.db
set RETENTION_DAYS=30
set BACKUP_PREFIX=test_results_backup

REM Create backup directory if it doesn't exist
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

REM Generate timestamp
set TIMESTAMP=%date:~-4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set BACKUP_NAME=%BACKUP_PREFIX%_%TIMESTAMP%
set BACKUP_FILE=%BACKUP_DIR%\%BACKUP_NAME%.zip

echo ======================================
echo Test Results Archive - Backup
echo ======================================
echo Timestamp: %date% %time%
echo Backup file: %BACKUP_FILE%
echo.

REM Check if database exists
if not exist "%DATABASE_FILE%" (
    echo Warning: Database file not found: %DATABASE_FILE%
    echo Skipping database backup.
    set DATABASE_EXISTS=false
) else (
    set DATABASE_EXISTS=true
)

REM Create backup
echo Creating backup...

if "%DATABASE_EXISTS%"=="true" (
    REM Backup with database
    powershell -Command "Compress-Archive -Path test_results.db,docker-compose.yml,nginx,schema.sql -DestinationPath '%BACKUP_FILE%' -Force -CompressionLevel Optimal"
) else (
    REM Backup without database
    powershell -Command "Compress-Archive -Path docker-compose.yml,nginx,schema.sql -DestinationPath '%BACKUP_FILE%' -Force -CompressionLevel Optimal"
)

REM Verify backup was created
if exist "%BACKUP_FILE%" (
    for %%F in ("%BACKUP_FILE%") do set BACKUP_SIZE=%%~zF
    set /a BACKUP_SIZE_MB=!BACKUP_SIZE! / 1048576
    echo Backup created successfully: %BACKUP_FILE% (!BACKUP_SIZE_MB! MB)
) else (
    echo Error: Backup failed!
    exit /b 1
)

REM Copy to "latest" backup
set LATEST_FILE=%BACKUP_DIR%\%BACKUP_PREFIX%_latest.zip
copy /Y "%BACKUP_FILE%" "%LATEST_FILE%" >nul
echo Latest backup copied to: %LATEST_FILE%

REM Clean up old backups (older than RETENTION_DAYS)
echo.
echo Cleaning up old backups (older than %RETENTION_DAYS% days)...
forfiles /p "%BACKUP_DIR%" /m "%BACKUP_PREFIX%_*.zip" /d -%RETENTION_DAYS% /c "cmd /c del @path" 2>nul
if %errorlevel% equ 0 (
    echo Old backups removed.
) else (
    echo No old backups to remove.
)

REM Count remaining backups
set BACKUP_COUNT=0
for %%F in (%BACKUP_DIR%\%BACKUP_PREFIX%_*.zip) do set /a BACKUP_COUNT+=1
echo Remaining backups: %BACKUP_COUNT%

REM List recent backups
echo.
echo Recent backups:
dir /B /O-D "%BACKUP_DIR%\%BACKUP_PREFIX%_*.zip" 2>nul | findstr /V "latest" | head -n 5

echo.
echo Backup complete!

endlocal

@echo off
REM Deployment script for Test Results Archive System (Windows)

setlocal enabledelayedexpansion

echo ======================================
echo Test Results Archive - Deployment
echo ======================================
echo.

REM Check if Docker is installed
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

where docker-compose >nul 2>nul
if %errorlevel% neq 0 (
    echo Error: Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Parse command
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=start

if "%COMMAND%"=="start" goto start
if "%COMMAND%"=="stop" goto stop
if "%COMMAND%"=="restart" goto restart
if "%COMMAND%"=="down" goto down
if "%COMMAND%"=="logs" goto logs
if "%COMMAND%"=="build" goto build
if "%COMMAND%"=="rebuild" goto rebuild
if "%COMMAND%"=="status" goto status
if "%COMMAND%"=="import" goto import
if "%COMMAND%"=="backup" goto backup
if "%COMMAND%"=="restore" goto restore
if "%COMMAND%"=="clean" goto clean
goto usage

:start
echo Starting services...
docker-compose up -d
echo.
echo Services started successfully!
echo.
echo Access the application at:
echo   - Web UI: http://localhost:80
echo   - API: http://localhost:80/api
echo   - API Docs: http://localhost:80/docs
echo.
echo Direct service access (without nginx):
echo   - Web: http://localhost:8080
echo   - API: http://localhost:8000
echo.
goto end

:stop
echo Stopping services...
docker-compose stop
echo Services stopped.
goto end

:restart
echo Restarting services...
docker-compose restart
echo Services restarted.
goto end

:down
echo Stopping and removing containers...
docker-compose down
echo Containers removed.
goto end

:logs
set SERVICE=%2
if "%SERVICE%"=="" (
    docker-compose logs -f
) else (
    docker-compose logs -f %SERVICE%
)
goto end

:build
echo Building Docker images...
docker-compose build --no-cache
echo Build complete.
goto end

:rebuild
echo Rebuilding and restarting services...
docker-compose down
docker-compose build --no-cache
docker-compose up -d
echo Rebuild complete.
goto end

:status
echo Service status:
docker-compose ps
goto end

:import
echo Running data import...
docker-compose exec api python sql_importer.py --scan output
echo Import complete.
goto end

:backup
echo Creating backup...
set BACKUP_DIR=backups
set BACKUP_FILE=backup_%date:~-4%%date:~-7,2%%date:~-10,2%_%time:~0,2%%time:~3,2%%time:~6,2%.zip

if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

echo Backing up database and configuration...
powershell -Command "Compress-Archive -Path test_results.db,docker-compose.yml,nginx -DestinationPath '%BACKUP_DIR%\%BACKUP_FILE%' -Force"

echo Backup created: %BACKUP_DIR%\%BACKUP_FILE%
goto end

:restore
set BACKUP_FILE=%2
if "%BACKUP_FILE%"=="" (
    echo Error: Please specify backup file to restore.
    echo Usage: deploy.bat restore ^<backup_file^>
    exit /b 1
)

if not exist "%BACKUP_FILE%" (
    echo Error: Backup file not found: %BACKUP_FILE%
    exit /b 1
)

echo Warning: This will overwrite existing data!
set /p CONFIRM="Are you sure you want to continue? (yes/no): "

if /i "%CONFIRM%"=="yes" (
    echo Stopping services...
    docker-compose stop

    echo Restoring from backup...
    powershell -Command "Expand-Archive -Path '%BACKUP_FILE%' -DestinationPath . -Force"

    echo Starting services...
    docker-compose start

    echo Restore complete.
) else (
    echo Restore cancelled.
)
goto end

:clean
echo Warning: This will remove all containers, volumes, and data!
set /p CONFIRM="Are you sure you want to continue? (yes/no): "

if /i "%CONFIRM%"=="yes" (
    docker-compose down -v
    echo Cleanup complete.
) else (
    echo Cleanup cancelled.
)
goto end

:usage
echo Usage: deploy.bat {start^|stop^|restart^|down^|logs^|build^|rebuild^|status^|import^|backup^|restore^|clean}
echo.
echo Commands:
echo   start     - Start all services
echo   stop      - Stop all services
echo   restart   - Restart all services
echo   down      - Stop and remove containers
echo   logs      - View logs (optionally specify service: logs api)
echo   build     - Build Docker images
echo   rebuild   - Rebuild images and restart services
echo   status    - Show service status
echo   import    - Run data import from output directory
echo   backup    - Create backup of database and config
echo   restore   - Restore from backup (requires backup file)
echo   clean     - Remove all containers and volumes (WARNING: deletes data)
exit /b 1

:end
endlocal

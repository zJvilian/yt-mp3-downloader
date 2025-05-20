@echo off
REM ───────────────────────────────────────────────────────────────────────────
REM restart-docker.bat
REM Stops docker-compose, rebuilds images, and brings it back up.
REM Place this file alongside docker-compose.yml and double-click to run.
REM ───────────────────────────────────────────────────────────────────────────

REM Switch to the directory containing this script
cd /d "%~dp0"

echo.
echo ========== Stopping containers ==========
docker-compose down

echo.
echo ========== Rebuilding images ==========
docker-compose build

echo.
echo ========== Starting containers ==========
docker-compose up -d

echo.
echo ========== Done ==========
pause

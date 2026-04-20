@echo off
REM Local deployment script for Autonomous Airdrop Bot (Windows)
REM This script helps you deploy the bots locally using Docker Compose

echo ==========================================
echo   Autonomous Airdrop Bot - Local Deployment
echo ==========================================
echo.

REM Check if .env file exists
if not exist .env (
    echo [ERROR] .env file not found!
    echo Please run "python setup_bot.py" first to create the .env file.
    exit /b 1
)

REM Check if data/wallets.enc exists
if not exist data\wallets.enc (
    echo [ERROR] Encrypted wallet store not found at data\wallets.enc
    echo Please run "python generate_wallets.py" to generate your wallets.
    exit /b 1
)

REM Create necessary directories
echo [INFO] Creating necessary directories...
if not exist data mkdir data
if not exist logs mkdir logs

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed. Please install Docker Desktop first.
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    docker compose version >nul 2>&1
    if %errorlevel% neq 0 (
        echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
        exit /b 1
    )
)

REM Build Docker images
echo [INFO] Building Docker images...
docker-compose build
if %errorlevel% neq 0 (
    echo [ERROR] Docker build failed.
    exit /b 1
)

REM Start the bots
echo [INFO] Starting the bots...
docker-compose up -d
if %errorlevel% neq 0 (
    echo [ERROR] Failed to start the bots.
    exit /b 1
)

echo.
echo ==========================================
echo   Deployment Complete!
echo ==========================================
echo.
echo To view logs:
echo   docker-compose logs -f
echo.
echo To stop the bots:
echo   docker-compose down
echo.
echo To restart the bots:
echo   docker-compose restart
echo.
echo To check status:
echo   docker-compose ps
echo.

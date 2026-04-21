@echo off
echo ===================================================
echo   RENDER DEPLOYMENT HELPER
echo ===================================================
echo.
echo Step 1: Opening Render Dashboard...
echo Step 2: Use these EXACT settings:
echo.
echo ---------------------------------------------------
echo  BLUEPRINT METHOD (EASIEST):
echo ---------------------------------------------------
echo 1. Go to: https://dashboard.render.com/blueprint
echo 2. Click: "New Blueprint Instance"
echo 3. Select: investment-tools repo
echo 4. Click: "Apply"
echo.
echo ---------------------------------------------------
echo  MANUAL METHOD (IF BLUEPRINT FAILS):
echo ---------------------------------------------------
echo Service Name: coinbot
echo Runtime: Docker
echo Plan: Free
echo Region: Ohio (US East)
echo Branch: main
echo Dockerfile Path: ./Dockerfile
echo.
echo Environment Variables:
echo   PORT=8080
echo   BOT_TYPE=coinbot
echo   CLAIM_INTERVAL_HOURS=1
echo   HEADLESS=true
echo   PYTHONUNBUFFERED=1
echo.
echo Health Check Path: /healthz
echo ---------------------------------------------------
echo.
start https://dashboard.render.com/blueprint
echo.
echo Browser opened to Render Blueprint page.
echo.
echo After deploy, your URL will be shown.
echo Copy that URL and run: setup_uptimerobot.bat
echo.
pause

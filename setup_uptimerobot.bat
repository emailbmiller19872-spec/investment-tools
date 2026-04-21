@echo off
echo ===================================================
echo   UPTIMEROBOT SETUP FOR 24/7 OPERATION
echo ===================================================
echo.
echo Step 1: Opening UptimeRobot signup...
start https://uptimerobot.com/
echo.
echo FOLLOW THESE STEPS:
echo ---------------------------------------------------
echo 1. Click "Start Monitoring For Free"
echo 2. Sign up with email/password
echo 3. Verify your email (check inbox)
echo 4. Click "Add New Monitor"
echo 5. Fill in:
echo.
echo    Monitor Type: HTTP(s)
echo    Friendly Name: Coinbot Render
echo    URL: https://coinbot-XXXX.onrender.com/healthz
echo           ^^^^^
echo           (Replace with your actual Render URL)
echo    Interval: Every 5 minutes (free max)
echo.
echo 6. Click "Create Monitor"
echo ---------------------------------------------------
echo.
echo This pings your bot every 5 mins to keep it awake 24/7!
echo.
pause

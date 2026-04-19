@echo off
echo ==========================================
echo  AUTONOMOUS AIRDROP CAPITAL BUILDER SETUP
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed. Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found

REM Install dependencies
echo.
echo Installing Python dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

REM Check Chrome
reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe" >nul 2>&1
if errorlevel 1 (
    echo WARNING: Chrome browser not found. Please install Google Chrome.
) else (
    echo [OK] Chrome found
)

REM Check ChromeDriver
chromedriver --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: ChromeDriver not found. It should be installed with selenium.
) else (
    echo [OK] ChromeDriver found
)

REM Create .env if not exists
if not exist .env (
    echo Creating .env template...
    (
    echo # Wallet
    echo WALLET_ADDRESS=your_wallet_address
    echo PRIVATE_KEY=your_private_key
    echo.
    echo # APIs
    echo TWITTER_API_KEY=your_twitter_key
    echo TWITTER_API_SECRET=your_twitter_secret
    echo TWITTER_ACCESS_TOKEN=your_access_token
    echo TWITTER_ACCESS_SECRET=your_access_secret
    echo TELEGRAM_API_ID=your_telegram_api_id
    echo TELEGRAM_API_HASH=your_telegram_api_hash
    echo TWOCAPTCHA_API_KEY=your_2captcha_key
    echo.
    echo # Proxies
    echo PROXIES=http://proxy1:port,http://proxy2:port
    echo.
    echo # Settings
    echo HEADLESS=true
    echo CHECK_INTERVAL_HOURS=6
    echo MAX_AIRDROPS_PER_CYCLE=10
    echo USER_AGENT_ROTATION=true
    echo CAPTCHA_SOLVING_ENABLED=true
    ) > .env
    echo [OK] .env created - Please configure your settings
)

echo.
echo Setup complete! Please:
echo 1. Configure your .env file with real API keys and wallet details
echo 2. Set up proxies if needed for anti-detection
echo 3. Run the bot with: python main.py
echo.
pause
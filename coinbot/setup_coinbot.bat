@echo off
echo ==========================================
echo      COINBOT SETUP FOR FAUCET AUTOMATION
echo ==========================================
echo.

REM Verify Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH. Install Python 3.8+ from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found

REM Upgrade pip and install dependencies
echo.
echo Installing Python dependencies...
python -m pip install --upgrade pip >nul 2>&1
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Dependency installation failed. Please check pip output above.
    pause
    exit /b 1
)
echo [OK] Dependencies installed

REM Check Chrome browser installation
echo.
where chrome >nul 2>&1
if errorlevel 1 (
    echo WARNING: Google Chrome was not found in PATH. Please install Chrome or verify the executable path.
) else (
    echo [OK] Chrome found
)

REM Create environment template if missing
echo.
if not exist .env (
    echo Creating .env template...
    (
    echo # Wallet
    echo WALLET_ADDRESSES=0xWallet1,0xWallet2
    echo WALLET_ADDRESS=your_wallet_address
    echo PRIVATE_KEY=your_private_key
    echo.
    echo # Ethereum / RPC provider
    echo ETH_PROVIDER_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY
    echo.
    echo # APIs
    echo TWOCAPTCHA_API_KEY=your_2captcha_key
    echo CAPSOLVER_API_KEY=your_capsolver_key
    echo.
    echo # Browser and driver
    echo BROWSER=chrome
    echo DRIVER_PATH=./chromedriver.exe
    echo BROWSER_DATA_DIR=C:\Users\%USERNAME%\AppData\Local\Google\Chrome\User Data
    echo BROWSER_PROFILE=Default
    echo.
    echo # Proxies (comma-separated)
    echo PROXIES=http://proxy1:port,http://proxy2:port
    echo.
    echo # Runtime settings
    echo HEADLESS=true
    echo CLAIM_INTERVAL_HOURS=1
    echo MAX_THREADS=1
    echo RETRY_COUNT=2
    echo RETRY_BACKOFF_SECONDS=5
    echo DEFAULT_WAIT_TIMEOUT=60
    echo CLOSE_AD_ATTEMPTS=1
    echo CLOSE_AD_RETRY_DELAY=5
    echo USER_AGENT_ROTATION=true
    echo CAPTCHA_SOLVING_ENABLED=true
    ) > .env
    echo [OK] .env template created
) else (
    echo .env already exists. Please open .env and verify your wallet, API keys, and proxy settings.
)

echo.
echo Setup complete.
echo Next steps:
echo 1. Open .env and replace placeholders with your real wallet, API keys, and proxy values.
echo 2. Ensure BROWSER_DATA_DIR and BROWSER_PROFILE are correct for your Chrome user profile.
echo 3. Run the bot with: python main.py
echo.
pause
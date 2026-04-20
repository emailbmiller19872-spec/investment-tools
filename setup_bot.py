#!/usr/bin/env python3
"""
Automated setup script for the Autonomous Airdrop Bot.
Run this script once to create all necessary files and verify the environment.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

# ---------- Configuration ----------
REQUIRED_PYTHON = (3, 8)
REQUIREMENTS_FILE = "requirements.txt"
ENV_TEMPLATE = """.env template created – edit with your real keys.

# Wallet Store (REQUIRED)
WALLET_STORE_PATH=data/wallets.enc
WALLET_STORE_KEY=your_wallet_store_password_here

# Web3 RPC (REQUIRED)
WEB3_RPC_URLS=https://mainnet.infura.io/v3/YOUR_INFURA_KEY,https://rpc.ankr.com/eth

# CAPTCHA solving (recommended)
TWOCAPTCHA_API_KEY=your_2captcha_key
CAPSOLVER_API_KEY=your_capsolver_key

# Proxy settings (optional)
PROXIES=http://user:pass@host:port,http://...

# Bot settings
HEADLESS=false
PORT=8080
USER_AGENT_ROTATION=true
CAPTCHA_SOLVING_ENABLED=true

# Consolidation settings (for coinbot -> airfarm transfer)
CONSOLIDATION_ENABLED=true
CONSOLIDATION_MIN_BALANCE_ETH=0.02
CONSOLIDATION_GAS_BUFFER_ETH=0.005
CONSOLIDATION_DELAY_MIN_SECONDS=10
CONSOLIDATION_DELAY_MAX_SECONDS=30

# Airfarm funding settings
AIRFARM_FUNDING_ENABLED=true
AIRFARM_MIN_FUND_BALANCE_ETH=0.03
AIRFARM_FUND_AMOUNT_ETH=0.06
AIRFARM_FUNDING_DELAY_MIN_SECONDS=10
AIRFARM_FUNDING_DELAY_MAX_SECONDS=25

# Schedule settings
CHECK_INTERVAL_HOURS=6
MAX_AIRDROPS_PER_CYCLE=10

# Email notifications (optional)
USER_EMAIL=you@example.com
EMAIL_ADDRESS=your_gmail@gmail.com
EMAIL_PASSWORD=your_app_password
NOTIFICATION_EMAIL=notify@example.com

# Tesseract OCR (optional – for image captchas)
TESSERACT_PATH=C:\\Program Files\\Tesseract-OCR\\tesseract.exe
"""

# ---------- Helper functions ----------
def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)

def check_python_version():
    print_header("Checking Python version")
    if sys.version_info[:2] < REQUIRED_PYTHON:
        print(f"ERROR: Python {REQUIRED_PYTHON[0]}.{REQUIRED_PYTHON[1]}+ required. You have {sys.version_info[0]}.{sys.version_info[1]}")
        sys.exit(1)
    print(f"✓ Python {sys.version_info[0]}.{sys.version_info[1]} – OK")

def create_directories():
    print_header("Creating required directories")
    dirs = ["data", "logs", "config"]
    for d in dirs:
        Path(d).mkdir(exist_ok=True)
        print(f"✓ Created /{d} (or already exists)")

def install_requirements():
    print_header("Installing Python dependencies")
    if not os.path.exists(REQUIREMENTS_FILE):
        print("⚠ requirements.txt not found. Creating it with standard packages...")
        with open(REQUIREMENTS_FILE, "w") as f:
            f.write("""selenium==4.15.2
web3==6.15.1
requests==2.31.0
python-dotenv==1.0.0
beautifulsoup4==4.12.2
lxml==4.9.3
schedule==1.2.0
telethon==1.32.1
tweepy==4.14.0
fake-useragent==1.4.0
requests-html==0.10.0
pytesseract==0.3.10
Pillow==10.1.0
undetected-chromedriver
twocaptcha
capsolver
cryptography==41.0.7
bip-utils==2.9.1
mnemonic==0.24
""")
    print("Running: pip install -r requirements.txt")
    result = subprocess.run([sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE])
    if result.returncode != 0:
        print("ERROR: pip install failed. Check your internet connection and try again.")
        sys.exit(1)
    print("✓ Dependencies installed")

def create_env_file():
    print_header("Creating .env template")
    if os.path.exists(".env"):
        overwrite = input(".env already exists. Overwrite? (y/N): ").strip().lower()
        if overwrite != "y":
            print("Keeping existing .env file.")
            return
    try:
        with open(".env", "w") as f:
            f.write(ENV_TEMPLATE)
        print("✓ .env template created – edit it with your real keys and configuration.")
    except PermissionError:
        print("❌ Permission denied: Cannot write to .env file")
        print("The file may be open in another program (e.g., your IDE).")
        print("Please close the file and run the script again, or create .env manually.")
        print("\nYou can create .env manually with the following content:")
        print("-" * 60)
        print(ENV_TEMPLATE)
        print("-" * 60)
    except Exception as e:
        print(f"❌ Error creating .env file: {e}")

def test_imports():
    print_header("Testing critical imports")
    errors = []
    modules = [
        "selenium",
        "web3",
        "requests",
        "dotenv",
        "bs4",
        "lxml",
        "schedule",
        "fake_useragent",
        "PIL",
        "cryptography",
        "bip_utils",
        "mnemonic",
    ]
    for mod in modules:
        try:
            __import__(mod)
            print(f"✓ {mod}")
        except ImportError as e:
            print(f"✗ {mod} – {e}")
            errors.append(mod)
    if errors:
        print(f"\n⚠️ Some modules failed to import. Run 'pip install -r {REQUIREMENTS_FILE}' manually.")
    else:
        print("✓ All critical modules imported successfully")

def check_chrome():
    print_header("Checking Chrome browser")
    if platform.system() == "Windows":
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        found = any(os.path.exists(p) for p in chrome_paths)
    elif platform.system() == "Darwin":  # macOS
        found = os.path.exists("/Applications/Google Chrome.app")
    else:  # Linux
        found = shutil.which("google-chrome") is not None or shutil.which("chromium-browser") is not None
    if found:
        print("✓ Chrome browser found.")
    else:
        print("⚠ Chrome not detected. The bot may fail if you run with HEADLESS=false.")
        print("  Please install Google Chrome from https://www.google.com/chrome/")

def show_next_steps():
    print_header("Setup complete – next steps")
    print("""
1. Run 'python wallet_setup.py' to generate your wallets with BIP-39 mnemonic.
   This will create an encrypted wallet store at data/wallets.enc

2. Edit the .env file with:
   - WALLET_STORE_KEY (the password you set during wallet generation)
   - WEB3_RPC_URLS (your Infura or other RPC endpoints)
   - CAPTCHA solver keys (recommended for reliability)
   - Other settings as needed

3. For local deployment with Docker:
   docker-compose up -d

4. For cloud deployment (Oracle Cloud):
   - Configure terraform/variables.tf with your OCI credentials
   - Run: terraform init && terraform apply

5. To run the bots directly:
   - Coinbot (faucet collector): cd farming-bot/coinbot && python main.py
   - Airfarm (airdrop farmer): cd farming-bot/airfarm && python main.py

For first run, set HEADLESS=false to see the browser in action.
To run 24/7 on a cloud VPS, set HEADLESS=true and use a process manager (systemd).

Happy farming! 🚀
""")

# ---------- Main ----------
def main():
    print_header("Autonomous Airdrop Bot – Automated Setup")
    check_python_version()
    create_directories()
    install_requirements()
    create_env_file()
    test_imports()
    check_chrome()
    show_next_steps()

if __name__ == "__main__":
    main()

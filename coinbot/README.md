# Autonomous Faucet Collector

A standalone faucet automation variant built from the copied desktop project. It targets faucet claim pages and handles claim retries, proxy rotation, configurable faucet definitions, CAPTCHA solving, and wallet tracking.

## Features

- **Faucet Definitions**: Loads faucet metadata from `faucets.json` instead of scraping unpredictable pages
- **Top Targets for 2026**: Includes sample source definitions for FreeBitco.in, Cointiply, FaucetCrypto, FireFaucet, CoinPayU, FaucetPay, DutchyCorp, and StakeCube
- **Claim Automation**: Visits faucet pages, fills wallet fields, clicks claim buttons, and submits forms
- **Wallet Integration**: Supports multiple wallet addresses from `.env`
- **Proxy & Anti-Detection**: Rotates IPs and user agents to reduce blocking
- **Stealth Browser**: Runs Selenium through `undetected-chromedriver` with auto-managed WebDriver
- **CAPTCHA Solving**: Supports paid solving via 2Captcha and configurable solver integration
- **Continuous Operation**: Runs on a schedule and recovers from failures
- **Database Tracking**: Records claimed faucets so it does not repeat the same URL

## Top Faucet Targets for 2026

Based on payout consistency and automation suitability, the primary faucet targets include:

- **Cointiply** — BTC, LTC, DOGE, DASH; frequent claim windows and long-term trust.
- **FireFaucet** — 15+ coins including ADA, BTC, ETH, LTC, TRX, DOGE; supports auto-claim behavior.
- **FreeBitco.in** — BTC; hourly claims and historical reliability.
- **CoinPayU** — 7+ coins; reward-based tasks and ad-viewing.
- **FaucetPay** — multi-coin payout gateway used by many faucet partners.
- **DutchyCorp** — crypto faucet network with a consistent reward flow.
- **StakeCube** — large altcoin variety with variable faucet rewards.

## Additional Automation Tools Worth Exploring

- **Browser Automation Studio (BAS)**: Visual automation with fingerprint switching and CAPTCHA handling.
- **Tampermonkey scripts**: Useful for lightweight browser-based faucet scripting.
- **Dedicated Python faucet loaders**: Use `faucets.json` to define selectors and page flows.

## Security & Important Warnings

- Use dedicated burner wallets only; never expose your primary wallet.
- Avoid detected proxies and VPNs; prefer residential IPs when available.
- Watch minimum withdrawal thresholds before scaling faucet claims.
- Do not share private keys, seed phrases, or passwords.
- Keep Chrome, browser drivers, and automation scripts updated.

## Setup

1. Run the setup script: `setup.bat` (Windows) or configure manually
2. Install Python 3.8+ and dependencies: `pip install -r requirements.txt`
3. Install Chrome browser (required for Selenium)
4. Configure `.env` with your API keys, wallet details, and runtime settings
5. Configure `faucets.json` with the faucet sites and selectors to claim
6. Set up proxies (optional but recommended for anti-detection)
7. Run: `python main.py`

## Configuration (.env)

```env
# Wallet
WALLET_ADDRESSES=0xWallet1,0xWallet2
WALLET_ADDRESS=your_wallet_address
PRIVATE_KEY=your_private_key
FARM_PRIVATE_KEYS=your_farm_wallet_private_key1,your_farm_wallet_private_key2
MASTER_WALLET_ADDRESS=0xYourMainOperationalWallet
MASTER_PRIVATE_KEY=your_master_wallet_private_key

# Ethereum / RPC provider
ETH_PROVIDER_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY

# APIs
TWOCAPTCHA_API_KEY=your_2captcha_key
CAPSOLVER_API_KEY=your_capsolver_key

# Browser and driver
BROWSER=chrome
DRIVER_PATH=./chromedriver.exe
BROWSER_DATA_DIR=C:\Users\<USERNAME>\AppData\Local\Google\Chrome\User Data
BROWSER_PROFILE=Default

# Proxy settings
PROXIES=http://proxy1:port,http://proxy2:port

# Runtime settings
HEADLESS=true
CLAIM_INTERVAL_HOURS=1
CONSOLIDATION_ENABLED=true
CONSOLIDATION_INTERVAL_MINUTES=60
MIN_CONSOLIDATION_BALANCE_ETH=0.01
CONSOLIDATION_GAS_BUFFER_ETH=0.002
CONSOLIDATION_DELAY_MIN_SECONDS=10
CONSOLIDATION_DELAY_MAX_SECONDS=30
MAX_THREADS=1
RETRY_COUNT=2
RETRY_BACKOFF_SECONDS=5
DEFAULT_WAIT_TIMEOUT=60
CLOSE_AD_ATTEMPTS=1
CLOSE_AD_RETRY_DELAY=5
USER_AGENT_ROTATION=true
CAPTCHA_SOLVING_ENABLED=true
```

## Consolidation Engine

This project now includes a consolidation engine that automatically sweeps ETH from your farm wallets into a master wallet.

- `WALLET_ADDRESSES` defines the farm wallets used by the faucet bot.
- `FARM_PRIVATE_KEYS` maps private keys to the same wallet list for sweep transactions.
- `MASTER_WALLET_ADDRESS` is the destination wallet for consolidated earnings.
- `CONSOLIDATION_ENABLED` turns the sweep engine on or off.
- `MIN_CONSOLIDATION_BALANCE_ETH` and `CONSOLIDATION_GAS_BUFFER_ETH` ensure only profitable sweeps occur.
- `CONSOLIDATION_INTERVAL_MINUTES` can schedule consolidation independently of faucet claims.

The engine runs after every faucet cycle and can also run on its own schedule for continuous fund pooling.

## Components

- `main.py`: Entry point, orchestrates the system
- `scraper.py`: Loads faucet definitions from `faucets.json`
- `task_automator.py`: Automates faucet claim interactions and form submission
- `wallet_manager.py`: Handles wallet configuration and balance tracking
- `proxy_manager.py`: Manages proxy rotation for anti-detection
- `captcha_solver.py`: Solves CAPTCHAs using 2Captcha
- `database.py`: Tracks faucet claims, balances, and transactions
- `utils.py`: Helper functions for delays, user agents, safe clicking
- `faucets.json`: Faucet definitions and page selector configuration
- `setup.bat`: Automated setup script

## How It Works

1. **Definition Load**: Reads faucet details and selectors from `faucets.json`
2. **Claim Loop**: Visits each configured faucet page with Selenium
3. **Action Execution**: Enters wallet addresses, clicks claim buttons, handles CAPTCHAs, and submits forms
4. **Tracking**: Records claimed URLs so the bot does not repeat the same faucet too often
5. **Scheduling**: Runs continuously on a configurable interval

## Security & Legal Notes

- Uses secure wallet management (never stores seed phrases in plain text)
- Implements anti-detection measures: random delays, user agent rotation, proxy rotation
- Mimics human behavior to avoid bot detection
- All actions logged for transparency
- Use at your own risk; automated participation may violate terms of service
- Ensure compliance with local laws regarding automated trading
- Consider using dedicated wallets and accounts for airdrop farming

## Troubleshooting

- **ChromeDriver issues**: Ensure Chrome and ChromeDriver versions match
- **CAPTCHA failures**: Check 2Captcha balance and API key
- **Proxy blocks**: Rotate proxies or add more
- **Wallet connection fails**: Verify private key and network settings
- **Rate limiting**: Increase delays in utils.py
- **Logs**: Check `logs/airdrop_bot.log` for detailed error information

## Advanced Configuration

- **Custom Airdrop Sources**: Add URLs to `scraper.py`
- **Task Customization**: Modify `task_automator.py` for specific airdrops
- **Exchange Integration**: Add API calls in `wallet_manager.py` for auto-selling
- **Notification System**: Integrate email/SMS alerts for new airdrops

## Disclaimer

This tool is for educational purposes. Airdrop participation involves risks including loss of funds, account bans, and legal issues. Always research airdrops manually before automated participation. The developers are not responsible for any financial losses or violations of terms of service.
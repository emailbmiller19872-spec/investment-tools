# Autonomous Airdrop Capital Builder

A fully autonomous system for discovering, participating in, and managing cryptocurrency airdrops to build capital. Handles all aspects including task automation, wallet management, proxy rotation, CAPTCHA solving, and violation avoidance.

## Features

- **Automated Discovery**: Scrapes multiple airdrop listing sites
- **Multi-Platform Automation**: Handles web forms, Telegram, Twitter tasks
- **Wallet Integration**: Secure wallet management with Web3
- **Proxy & Anti-Detection**: Rotates IPs, user agents, mimics human behavior
- **CAPTCHA Solving**: Integrates with 2Captcha for automated solving
- **Task Completion**: Automates follows, joins, quizzes, wallet connections
- **Capital Tracking**: Monitors wallet balances and token values
- **Error Handling & Recovery**: Comprehensive logging, retries, workarounds
- **Violation Avoidance**: Built-in measures to prevent bans (proxies, delays, etc.)
- **Continuous Operation**: Scheduled runs without interruption
- **Database Tracking**: SQLite database for airdrop history and balances

## Setup

1. Run the setup script: `setup.bat` (Windows) or configure manually
2. Install Python 3.8+ and dependencies: `pip install -r requirements.txt`
3. Install Chrome browser (required for Selenium)
4. Configure `.env` with your API keys, wallet details, etc.
5. Set up proxies (optional but recommended for anti-detection)
6. Run: `python main.py`

## Configuration (.env)

```env
# Wallet store encryption
WALLET_STORE_KEY=your_secure_encryption_key
WALLET_STORE_FILE=data/wallets.enc

# Optional fallback wallet file if encrypted store is not used
WALLET_FILE=data/wallets.json

# Master consolidation wallet
MASTER_WALLET_ADDRESS=your_master_wallet_address
CONSOLIDATION_ENABLED=true
MIN_CONSOLIDATION_BALANCE_ETH=0.02
CONSOLIDATION_GAS_BUFFER_ETH=0.005
CONSOLIDATION_MIN_MINUTES=15
CONSOLIDATION_MAX_MINUTES=360

# Optional middleware wallet to break farm-to-master links
MIDDLEWARE_WALLET_ADDRESS=your_middleware_wallet_address
MIDDLEWARE_WALLET_PRIVATE_KEY=your_middleware_wallet_private_key

# APIs
TWITTER_API_KEY=your_twitter_key
TWITTER_API_SECRET=your_twitter_secret
TWITTER_ACCESS_TOKEN=your_access_token
TWITTER_ACCESS_SECRET=your_access_secret
TELEGRAM_API_ID=your_telegram_api_id
TELEGRAM_API_HASH=your_telegram_api_hash
TWOCAPTCHA_API_KEY=your_2captcha_key

# Proxies (comma-separated)
PROXIES=http://proxy1:port,http://proxy2:port

# Settings
HEADLESS=true
CHECK_INTERVAL_HOURS=6
MAX_AIRDROPS_PER_CYCLE=10
USER_AGENT_ROTATION=true
CAPTCHA_SOLVING_ENABLED=true
```

## Wallet Setup

Use `wallet_setup.py` to generate deterministic wallets from a BIP-39 mnemonic and encrypt the wallet store.

Example:

```bash
python wallet_setup.py --words 12 --count 5 --output data/wallets.enc
```

This script will prompt for `WALLET_STORE_KEY` if it is not already set in your environment.

If you need to verify the wallet generation process, add `--plaintext` to write a temporary plaintext file, then delete that file after verification.

Encrypted wallet storage is preferred for production deployment and prevents private keys from being stored in plaintext in the bot repository.


## Components

- `main.py`: Entry point, orchestrates the system
- `scraper.py`: Discovers new airdrops from multiple sources
- `decision_engine.py`: Analyzes and scores airdrops based on 2026 criteria (protocol fundamentals, tokenomics, team/backers, eligibility, community sentiment, on-chain difficulty)
- `task_automator.py`: Automates participation tasks (forms, social media, wallets)
- `wallet_manager.py`: Handles wallet connections and balance tracking
- `proxy_manager.py`: Manages proxy rotation for anti-detection
- `captcha_solver.py`: Solves CAPTCHAs using 2Captcha or CapSolver
- `database.py`: Tracks airdrops, balances, and transactions
- `utils.py`: Helper functions for delays, user agents, safe clicking
- `setup.bat`: Automated setup script

## How It Works

1. **Discovery**: Scrapes airdrop listings from multiple websites
2. **Analysis & Scoring**: Decision engine evaluates each airdrop based on protocol fundamentals, tokenomics, team quality, eligibility criteria, community sentiment, and task difficulty
3. **Prioritization**: Filters and ranks airdrops, focusing only on high-potential opportunities above the score threshold
4. **Automation**: Visits selected airdrop pages and completes required tasks:
   - Following social media accounts
   - Joining Telegram/Discord channels
   - Connecting wallets to dApps
   - Filling forms and solving CAPTCHAs
   - Submitting entries
5. **Tracking**: Records participation and monitors wallet balances
6. **Scheduling**: Runs continuously with configurable intervals

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
- **Decision Engine Tuning**: Adjust scoring weights in `decision_engine.py` and set `MIN_SCORE_THRESHOLD` in `.env` (default: 50)
- **Consolidation Settings**: Enable `CONSOLIDATION_ENABLED`, set `MASTER_WALLET_ADDRESS`, and optionally configure `MIDDLEWARE_WALLET_ADDRESS` / `MIDDLEWARE_WALLET_PRIVATE_KEY` to break direct farm-to-master links

## Decision Engine (2026 Intelligence Layer)

The decision engine analyzes airdrops using six key criteria:

- **Protocol Fundamentals** (25 points): Category leaders in trending sectors (DePIN, RWA, modular blockchains)
- **Tokenomics & Community** (20 points): Projects allocating >10% to community, fair distributions
- **Team & Backers** (20 points): Known teams with top-tier VC funding (a16z, Paradigm, etc.)
- **Eligibility & Sybil Resistance** (15 points): Clear, fair rules without excessive barriers
- **Community Sentiment** (10 points): Active social media engagement and genuine community
- **On-Chain Difficulty** (10 points): Balanced task complexity vs. reward potential

Only airdrops scoring above the threshold (configurable) are farmed, ensuring focus on high-potential opportunities.

### High-Potential 2026 Testnets

The decision engine includes built-in knowledge of promising 2026 projects:

- **Canopy Network ($CNPY)**: Appchain testnet with confirmed token airdrop and rewards hub
- **Settlr ($STLR)**: Risk-free paper trading on Hyperliquid testnet, 900M tokens allocated
- **Pharos Network ($PHRS)**: On-chain quests with DEX swaps and RWA lending
- **DataHaven ($HAVE)**: Confirmed tokenomics and airdrop, simple testnet activities
- **Zama (AI)**: FHE testnet for privacy-preserving machine intelligence

## Disclaimer

This tool is for educational purposes. Airdrop participation involves risks including loss of funds, account bans, and legal issues. Always research airdrops manually before automated participation. The developers are not responsible for any financial losses or violations of terms of service.
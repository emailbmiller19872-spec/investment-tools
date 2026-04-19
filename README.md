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
# Wallet
WALLET_ADDRESS=your_wallet_address
PRIVATE_KEY=your_private_key

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

## Components

- `main.py`: Entry point, orchestrates the system
- `scraper.py`: Discovers new airdrops from multiple sources
- `task_automator.py`: Automates participation tasks (forms, social media, wallets)
- `wallet_manager.py`: Handles wallet connections and balance tracking
- `proxy_manager.py`: Manages proxy rotation for anti-detection
- `captcha_solver.py`: Solves CAPTCHAs using 2Captcha
- `database.py`: Tracks airdrops, balances, and transactions
- `utils.py`: Helper functions for delays, user agents, safe clicking
- `setup.bat`: Automated setup script

## How It Works

1. **Discovery**: Scrapes airdrop listings from multiple websites
2. **Filtering**: Checks database to avoid duplicate participation
3. **Automation**: Visits airdrop pages and completes required tasks:
   - Following social media accounts
   - Joining Telegram/Discord channels
   - Connecting wallets to dApps
   - Filling forms and solving CAPTCHAs
   - Submitting entries
4. **Tracking**: Records participation and monitors wallet balances
5. **Scheduling**: Runs continuously with configurable intervals

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

## Deployment Pipeline

This repository now includes a full deploy pipeline for Docker + GitHub Actions.

1. **Dockerize the bot**
   - The root `Dockerfile` builds the bot with Python and Chromium for Selenium.
   - It installs dependencies from `requirements.txt` and runs `main.py`.

2. **Automated CI/CD**
   - `.github/workflows/deploy.yml` builds and pushes the `airfarm` container image to Docker Hub.
   - On every push to `main`, GitHub Actions deploys the latest image to your OCI VM.

3. **Multi-bot orchestration**
   - `docker-compose.yml` defines `coinbot` and `airfarm` services.
   - The remote deploy step starts `coinbot` first and waits until a wallet health check passes before launching `airfarm`.

4. **Infrastructure as Code**
   - `terraform/main.tf`, `terraform/variables.tf`, and `terraform/outputs.tf` provide a starting OCI deployment template.
   - Use `terraform init`, `terraform plan`, and `terraform apply` to provision your free Oracle Cloud VM.

## GitHub Secrets Required

Add these secrets to your repository settings under `Settings > Secrets and variables > Actions`:

- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`
- `SERVER_IP`
- `SSH_PRIVATE_KEY`
- `MASTER_WALLET_ADDRESS`
- `MIN_BALANCE_THRESHOLD`
- `RPC_URL`

## Notes

- Keep `.env` files and private keys out of git.
- The Docker image uses headless Chromium so the bot can run without a display.
- The remote deploy script assumes Docker and Docker Compose are installed on the OCI VM.

## Disclaimer

This tool is for educational purposes. Airdrop participation involves risks including loss of funds, account bans, and legal issues. Always research airdrops manually before automated participation. The developers are not responsible for any financial losses or violations of terms of service.
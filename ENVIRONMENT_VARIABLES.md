# Environment Variables for Render Deployment

## Required Variables (Both Services)

Add these in Render dashboard for both `coinbot` and `airfarm` worker services:

### Authentication & Wallet
- `WALLET_ADDRESSES` - Comma-separated list of wallet addresses
- `PRIVATE_KEY` - Private key for wallet operations
- `MASTER_WALLET_ADDRESS` - Master wallet for consolidation

### Anti-Detection
- `HEADLESS` - Set to `true` for headless browser mode
- `PROXIES` - Comma-separated residential proxy URLs (e.g., `http://proxy1:port,http://proxy2:port`)
- `CAPSOLVER_API_KEY` - Your Capsolver API key for captcha solving

### Service-Specific (Auto-set by render.yaml)
- `BOT_TYPE` - `coinbot` or `airfarm` (automatically set by render.yaml)
- `PYTHONUNBUFFERED` - Set to `1` (automatically set by render.yaml)

## Optional Variables

### Coinbot Specific
- `CLAIM_INTERVAL_HOURS` - Interval between faucet claims (default: 1)
- `CONSOLIDATION_INTERVAL_MINUTES` - Consolidation check interval in minutes (default: 0)

### Airfarm Specific
- `CHECK_INTERVAL_HOURS` - Interval between airdrop checks (default: 6)

### Both Services
- `CONSOLIDATION_ENABLED` - Enable wallet consolidation (default: true)
- `CONSOLIDATION_MIN_BALANCE_ETH` - Minimum balance to trigger consolidation (default: 0.02)
- `CONSOLIDATION_GAS_BUFFER_ETH` - Gas buffer for consolidation (default: 0.002)

## Setup Steps

1. Go to Render Dashboard
2. Select the worker service (coinbot or airfarm)
3. Navigate to "Environment" tab
4. Add each variable as a key-value pair
5. Redeploy the service

## Security Notes

- Never commit `.env` files to git
- Use Render's environment variable encryption
- Rotate API keys regularly
- Use separate wallets for each service if possible

# Investment Tools - Automated Crypto Bots

Automated cryptocurrency bots for faucet claiming (coinbot) and airdrop farming (airfarm) with anti-detection features.

## Features

- **Coinbot**: Automated faucet claiming and consolidation
- **Airfarm**: Automated airdrop participation and farming
- **Anti-detection**: Headless browser, residential proxies, random delays
- **Auto-consolidation**: Automatic wallet balance consolidation
- **24/7 Operation**: Deployed on Render for continuous operation

## Quick Deploy to Render

1. **Repository is already set up**: https://github.com/emailbmiller19872-spec/investment-tools

2. **Deploy to Render**:
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click **New +** → **Web Service**
   - Connect GitHub repository: `emailbmiller19872-spec/investment-tools`
   - Render will auto-detect `render.yaml` and create 2 worker services
   - Click **Create Web Service**

3. **Configure Environment Variables**:
   - See [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) for required variables
   - Add variables in Render dashboard for both `coinbot` and `airfarm` services
   - Redeploy after adding variables

## Architecture

- `main.py`: Orchestrator that runs either coinbot or airfarm based on `BOT_TYPE`
- `coinbot/`: Faucet claiming bot
- `airfarm/`: Airdrop farming bot
- `render.yaml`: Render deployment configuration
- `Dockerfile`: Container configuration with Chromium and Python dependencies

## Anti-Detection Features

- **Headless Browser**: Runs Chromium in headless mode
- **Residential Proxies**: Rotate through multiple residential proxies
- **Random Delays**: Random timing between actions
- **Undetected Chrome**: Uses undetected-chromedriver

## Environment Variables

Required for both services:
- `WALLET_ADDRESSES`: Comma-separated wallet addresses
- `PRIVATE_KEY`: Private key for wallet operations
- `MASTER_WALLET_ADDRESS`: Master wallet for consolidation
- `HEADLESS`: Set to `true` for headless mode
- `PROXIES`: Comma-separated residential proxy URLs
- `CAPSOLVER_API_KEY`: Capsolver API key for captcha solving

See [ENVIRONMENT_VARIABLES.md](ENVIRONMENT_VARIABLES.md) for complete list.

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run coinbot locally
BOT_TYPE=coinbot python main.py

# Run airfarm locally
BOT_TYPE=airfarm python main.py
```

## Deployment Notes

- **Free Tier**: Render free tier spins down after 15min inactivity
- **Paid Tier**: Recommended for 24/7 operation ($7/month Starter plan)
- **Health Checks**: Worker services don't require health checks
- **Logs**: View logs in Render dashboard for each service

## Troubleshooting

- **Build fails**: Check Render build logs for dependency issues
- **Bot not starting**: Check environment variables are set correctly
- **Proxy issues**: Verify proxy URLs are accessible
- **Captcha failures**: Check CAPSOLVER_API_KEY is valid

## Security

- Never commit `.env` files to git
- Use Render's encrypted environment variables
- Rotate API keys regularly
- Use separate wallets for each service

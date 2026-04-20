# Render Deployment Instructions

## Prerequisites
- Render account (free tier available)
- GitHub account with repository connected to Render
- All environment variables from `.env.example` configured

## Quick Deploy Steps

### 1. Push to GitHub
Ensure your repository is pushed to GitHub and connected to Render.

### 2. Create Render Web Service
1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click **New +** → **Web Service**
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Review the configuration:
   - **Name**: airdrop-bot (or your preferred name)
   - **Region**: Choose nearest region
   - **Branch**: main
   - **Runtime**: Docker
   - **Plan**: Free (or paid for better performance)

### 3. Configure Environment Variables
In the Render dashboard, add these environment variables:

**Required:**
- `WALLET_STORE_PATH` = `data/wallets.enc`
- `WALLET_STORE_KEY` = your wallet store password
- `TWOCAPTCHA_API_KEY` = your 2captcha API key
- `OCR_SPACE_API_KEY` = your OCR Space API key
- `WEB3_RPC_URLS` = comma-separated RPC URLs (e.g., `https://mainnet.infura.io/v3/YOUR_KEY,https://rpc.ankr.com/eth`)

**Optional (from .env.example):**
- `PROXIES` = comma-separated proxy URLs
- `USER_AGENT_ROTATION` = `true`
- `AIRFARM_FUNDING_ENABLED` = `true`
- `AIRFARM_MIN_FUND_BALANCE_ETH` = `0.03`
- `AIRFARM_FUND_AMOUNT_ETH` = `0.06`
- `CONSOLIDATION_ENABLED` = `true`
- `CONSOLIDATION_MIN_BALANCE_ETH` = `0.02`
- `CONSOLIDATION_GAS_BUFFER_ETH` = `0.002`
- `CHECK_INTERVAL_HOURS` = `6`
- `MAX_AIRDROPS_PER_CYCLE` = `10`

### 4. Deploy
Click **Create Web Service**. Render will:
- Build the Docker image
- Start the container
- Run health checks on `/healthz`

### 5. Monitor Deployment
- View logs in the Render dashboard
- Health check available at `https://your-app-name.onrender.com/healthz`
- The bot runs continuously, checking for airdrops every 6 hours (configurable)

## Important Notes

### Free Tier Limitations
- Free tier spins down after 15 minutes of inactivity
- Cold starts can take 30-60 seconds
- For continuous operation, consider the Starter plan ($7/month)

### Wallet Setup
If you need to generate the encrypted wallet store:
```bash
python wallet_setup.py --input data/wallets.json --output data/wallets.enc --key your_password
```
Then commit `data/wallets.enc` to your repository or use Render's disk storage.

### Data Persistence
- Render's free tier does not include persistent disk storage
- For wallet files and databases, consider:
  - Using Render Disk (paid add-on)
  - Storing data in external services (S3, database)
  - Using environment variables for sensitive data

### Troubleshooting
- **Build fails**: Check Render build logs for dependency issues
- **Health check fails**: Ensure the app listens on port 8080
- **Bot not running**: Check application logs in Render dashboard
- **Spinning down**: Upgrade to paid plan for continuous operation

## Alternative: Manual Deploy Without render.yaml
If you prefer manual configuration:
1. Create Web Service in Render
2. Select **Docker** as runtime
3. Set Docker context to `/`
4. Set Dockerfile path to `./Dockerfile`
5. Configure environment variables manually
6. Set health check path to `/healthz`

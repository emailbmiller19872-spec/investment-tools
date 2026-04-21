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
   - **Name**: coinbot (or your preferred name)
   - **Region**: Choose nearest region
   - **Branch**: main
   - **Runtime**: Docker
   - **Plan**: Free (or paid for true 24/7)

### 3. Configure Environment Variables
In the Render dashboard, add/update these environment variables:

**Required:**
- `PORT` = `8080` (already set in render.yaml)
- `DATABASE_URL` = auto-set from database
- `WALLET_ADDRESSES` = your farm wallet addresses (comma-separated)
- `FARM_PRIVATE_KEYS` = private keys for farm wallets
- `MASTER_WALLET_ADDRESS` = your master wallet
- `MASTER_PRIVATE_KEY` = master wallet private key
- `ETH_PROVIDER_URLS` = RPC endpoints

**Optional:**
- `CLAIM_INTERVAL_HOURS` = `1` (how often to claim faucets)
- `CONSOLIDATION_INTERVAL_MINUTES` = `30` (how often to consolidate funds)
- `CONSOLIDATION_ENABLED` = `true`
- `HEADLESS` = `true`
- `TWOCAPTCHA_API_KEY` = for CAPTCHA solving
- `PROXIES` = comma-separated proxy URLs

### 4. Deploy
Click **Create Web Service**. Render will:
- Build the Docker image
- Start the container
- Run health checks on `/healthz`

### 5. Monitor Deployment
- View logs in the Render dashboard
- Health check: `https://your-app-name.onrender.com/healthz`
- Status page: `https://your-app-name.onrender.com/status`

---

## 24/7 Operation Options

### Option 1: Free Tier with Ping Service (Recommended)
Render's free tier spins down after 15 minutes of inactivity. Use the included ping service:

**On your local computer or another server, run:**
```bash
# Windows
start_ping_service.bat

# Linux/Mac
python ping_service.py
```

Or set `RENDER_SERVICE_URL` and run the ping service anywhere:
```bash
set RENDER_SERVICE_URL=https://coinbot.onrender.com
python ping_service.py
```

The ping service sends a request every 10 minutes to keep the service awake.

### Option 2: Use UptimeRobot (Free Alternative)
1. Go to [UptimeRobot](https://uptimerobot.com/)
2. Create a free account
3. Add a monitor:
   - Type: HTTP(s)
   - URL: `https://your-app-name.onrender.com/healthz`
   - Interval: Every 5 minutes
4. This will keep your service awake 24/7

### Option 3: Upgrade to Starter Plan ($7/month)
- No spin-down
- True 24/7 operation
- Better performance
- Upgrade in Render dashboard

---

## Important Notes

### Free Tier Limitations
- Spins down after 15 minutes without requests
- Cold starts take 30-60 seconds
- Use ping service or UptimeRobot to prevent spin-down

### Wallet Setup
**⚠️ SECURITY WARNING:** Private keys in environment variables are visible in Render dashboard. For production:
- Use Render's **Environment** section only
- Never commit keys to GitHub
- Consider using a secrets manager

### Data Persistence
- Free tier: Data stored in SQLite (may reset on redeploy)
- Paid tier: Add disk storage for persistent data
- Bot will recreate database automatically if missing

### Troubleshooting
| Issue | Solution |
|-------|----------|
| Build fails | Check Render build logs; ensure Flask added to requirements |
| Health check fails | Check `/healthz` endpoint returns 200 |
| Bot spinning down | Use ping service or upgrade plan |
| Chrome/driver errors | Headless mode enabled by default in Docker |
| Database errors | Will auto-create on first run |

---

## API Endpoints

Once deployed, these endpoints are available:

- `GET /` - Service info
- `GET /healthz` - Health check (for Render)
- `GET /status` - Detailed bot status

Example response from `/status`:
```json
{
  "status": "idle",
  "last_run": "2024-01-15T10:30:00",
  "claims_today": 5,
  "total_claims": 150,
  "recent_errors": []
}
```

## Alternative: Manual Deploy Without render.yaml
1. Create Web Service in Render
2. Select **Docker** as runtime
3. Set Docker context to `/`
4. Set Dockerfile path to `./Dockerfile`
5. Set health check path to `/healthz`
6. Add environment variables manually
7. Set `PORT` to `8080`

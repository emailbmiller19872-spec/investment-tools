# Deployment Instructions for Automatic Bot Pipeline

## 1. Prerequisites
- Python 3.9+ installed locally
- Docker installed and running
- Git installed
- Chrome or Chromium installed for local testing
- Docker Hub account for image publishing
- Oracle Cloud VM with public IP and SSH access for deployment

## 2. Clone repository
```powershell
cd C:\Users\charl\Desktop
git clone <your-repo-url> autonomous-airdrop-capital-builder
cd autonomous-airdrop-capital-builder
```

## 2.1 Deploy with Koyeb (GitHub login, no credit card required)
1. Sign in at `https://app.koyeb.com/auth/signup` using GitHub.
2. Create a new application and import this repository from GitHub.
3. Choose Docker build and point to `Dockerfile` in the repo root.
4. Set the startup command to:
```sh
python main.py
```
5. Set `PORT=8080` and the required runtime variables from `.env.example`.
6. Deploy the app.

## 3. Required GitHub Secrets
Add these secrets in GitHub under `Settings > Secrets and variables > Actions`:

- `DOCKER_USERNAME` = your Docker Hub username
- `DOCKER_PASSWORD` = your Docker Hub password or access token
- `SERVER_IP` = public IP of your OCI VM
- `SSH_PRIVATE_KEY` = private SSH key for `ubuntu` login
- `COINBOT_ENV` = newline-separated environment variables for coinbot
- `AIRFARM_ENV` = newline-separated environment variables for airfarm

### Optional (health / monitoring)
- `MASTER_WALLET_ADDRESS`
- `MIN_BALANCE_THRESHOLD`
- `RPC_URL`

## 4. Recommended `COINBOT_ENV` / `AIRFARM_ENV` layout
Use the same core runtime variables for both services, then add service-specific values if needed.

Example content for `COINBOT_ENV` and `AIRFARM_ENV`:
```env
WALLET_STORE_PATH=data/wallets.enc
WALLET_STORE_KEY=your_wallet_store_password
TWOCAPTCHA_API_KEY=your_2captcha_key
OCR_SPACE_API_KEY=your_ocr_space_api_key
WEB3_RPC_URLS=https://mainnet.infura.io/v3/YOUR_INFURA_KEY,https://rpc.ankr.com/eth
HEADLESS=true
PROXIES=http://proxy1:port,http://proxy2:port
CONSOLIDATION_ENABLED=true
CONSOLIDATION_MIN_BALANCE_ETH=0.02
CONSOLIDATION_GAS_BUFFER_ETH=0.002
```

If you need a separate service setting for `coinbot` only, add it to `COINBOT_ENV`.

## 5. Build and test locally
From the repo root, run:
```powershell
docker build -t yourdockerhub/coinbot:latest -t yourdockerhub/airfarm:latest .
```

To test locally with headless disabled:
```powershell
docker run --rm --env HEADLESS=false --env-file coinbot.env yourdockerhub/coinbot:latest
```

If you want to test the second service with the same image:
```powershell
docker run --rm --env HEADLESS=false --env-file airfarm.env yourdockerhub/airfarm:latest
```

## 6. Push images to Docker Hub
```powershell
docker login --username yourdockerhub

docker push yourdockerhub/coinbot:latest
docker push yourdockerhub/airfarm:latest
```

## 7. Deploy automatically with GitHub Actions
The repo already contains a workflow at `.github/workflows/deploy.yml`.
When you push to `main`, GitHub Actions will:
- build the root Docker image
- push both `coinbot:latest` and `airfarm:latest`
- SSH into your OCI VM
- deploy a remote `docker-compose.yml`
- start `coinbot` and then `airfarm` after the health check passes

## 8. Verify deployment on OCI VM
SSH into the VM and run:
```bash
docker ps
docker compose -f /home/ubuntu/bot-deploy/docker-compose.yml ps
```

## 9. Notes
- The current build uses `server-healthcheck.sh` inside the image for `coinbot` health.
- `docker-compose.yml` ensures `airfarm` starts only after `coinbot` is healthy.
- `WALLET_STORE_KEY` and `WALLET_STORE_PATH` are required by current wallet loading code.
- If you need a wallet store file, use `wallet_setup.py` to generate `data/wallets.enc`.

## 10. Generating the encrypted wallet store
If you have a plaintext wallet JSON file, run:
```powershell
python wallet_setup.py --input data/wallets.json --output data/wallets.enc --key your_wallet_store_password
```

Then add `WALLET_STORE_PATH=data/wallets.enc` and `WALLET_STORE_KEY=your_wallet_store_password` to both `COINBOT_ENV` and `AIRFARM_ENV`.

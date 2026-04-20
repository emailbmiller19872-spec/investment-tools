# Farming Bot

This repository contains two autonomous bots:

- `coinbot/` — collects faucet rewards and funds the airfarm operational wallet
- `airfarm/` — farms airdrops and consolidates earnings to a final withdrawal wallet

The repository also includes a GitHub Actions deployment workflow to build both Docker images and deploy them to an Oracle Cloud VM.

## Repository Structure

```
.farming-bot/
├── .github/workflows/deploy.yml
├── coinbot/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── scraper.py
│   ├── task_automator.py
│   ├── wallet_manager.py
│   ├── consolidation.py
│   ├── proxy_manager.py
│   ├── captcha_solver.py
│   ├── free_captcha_solver.py
│   ├── database.py
│   ├── utils.py
│   └── faucets.json
└── airfarm/
    ├── Dockerfile
    ├── requirements.txt
    ├── main.py
    ├── orchestrator.py
    ├── scraper.py
    ├── task_automator.py
    ├── wallet_manager.py
    ├── consolidation.py
    ├── decision_engine.py
    ├── proxy_manager.py
    ├── captcha_solver.py
    ├── free_captcha_solver.py
    ├── database.py
    └── utils.py
```

## Setup

1. Create a private GitHub repository and push this folder.
2. Add the following GitHub Secrets in `Settings > Secrets and variables > Actions`:
   - `ORACLE_SSH_PRIVATE_KEY`
   - `ORACLE_VM_IP`
   - `DOCKER_USERNAME`
   - `DOCKER_TOKEN`
   - `COINBOT_ENV`
   - `AIRFARM_ENV`

### Secret values

- `COINBOT_ENV`: the contents of the remote `coinbot.env` file.
- `AIRFARM_ENV`: the contents of the remote `airfarm.env` file.

Each secret should contain a full `.env`-style file body, for example:

```env
WALLET_ADDRESSES=0xFaucetWallet1,0xFaucetWallet2
PRIVATE_KEY=your_private_key_for_faucet_wallets
MASTER_WALLET_ADDRESS=0xAirfarmOperationalWallet
CONSOLIDATION_ENABLED=true
MIN_CONSOLIDATION_BALANCE_ETH=0.01
CONSOLIDATION_GAS_BUFFER_ETH=0.002
HEADLESS=true
CLAIM_INTERVAL_HOURS=1
```

and:

```env
WALLET_ADDRESSES=0xAirfarmOperationalWallet
PRIVATE_KEY=private_key_of_that_wallet
MASTER_WALLET_ADDRESS=0xYourPersonalWithdrawalWallet
CONSOLIDATION_ENABLED=true
MIN_CONSOLIDATION_BALANCE_ETH=0.005
CONSOLIDATION_GAS_BUFFER_ETH=0.001
HEADLESS=true
CHECK_INTERVAL_HOURS=6
MAX_AIRDROPS_PER_CYCLE=5
CAPSOLVER_API_KEY=your_key_optional
```

## Deployment

On each push to `main`, GitHub Actions will:

1. build and push `coinbot` and `airfarm` Docker images
2. SSH to the Oracle VM
3. write `/home/ubuntu/coinbot.env` and `/home/ubuntu/airfarm.env`
4. stop and remove old containers
5. run the updated `coinbot` and `airfarm` containers

## Oracle VM One-Time Setup

Create an Oracle Cloud free-tier VM with Ubuntu 22.04, then install Docker:

```bash
sudo apt update && sudo apt install -y docker.io docker-compose
sudo systemctl enable docker && sudo systemctl start docker
sudo usermod -aG docker ubuntu
```

Set `ORACLE_VM_IP` to the VM public IP.

## Notes

- Keep private keys and secrets out of Git.
- The `coinbot` master wallet should be the airfarm operational wallet.
- The `airfarm` master wallet should be your final payout destination.
- Use proxies, headless mode, and randomized delays to reduce detection.

## Verification

After deployment, check logs on the VM:

```bash
docker logs coinbot
docker logs airfarm
```

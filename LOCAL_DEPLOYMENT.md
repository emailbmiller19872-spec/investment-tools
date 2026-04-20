# Autonomous Airdrop Bot - Local Deployment Guide

This guide will help you set up and deploy the Autonomous Airdrop Bot system locally using Docker Compose.

## System Overview

The system consists of two main components:

1. **Coinbot** - Faucet collection bot that earns from faucets and sweeps funds to a master wallet
2. **Airfarm** - Airdrop farming bot that spends funds to farm airdrops

The flow is: Coinbot wallets → Master wallet → Airfarm wallets

## Prerequisites

- Python 3.8 or higher
- Docker and Docker Compose installed
- Git (for cloning the repository)
- Chrome browser (for headless mode)

## Quick Start

### Step 1: Run the Automated Setup Script

```bash
python setup_bot.py
```

This will:
- Check your Python version
- Create required directories (data, logs, config)
- Install Python dependencies
- Create a .env template file
- Test critical imports
- Check for Chrome browser

### Step 2: Generate Your Wallets

```bash
python generate_wallets.py
```

This will:
- Generate a BIP-39 mnemonic (or use your existing one)
- Derive multiple wallet addresses from the mnemonic
- Create an encrypted wallet store at `data/wallets.enc`
- Prompt you to save your mnemonic securely

**IMPORTANT**: Save your mnemonic offline. Never share it!

### Step 3: Configure Your Environment

Edit the `.env` file with your actual configuration:

```bash
# Required
WALLET_STORE_KEY=your_wallet_store_password_here
WEB3_RPC_URLS=https://mainnet.infura.io/v3/YOUR_INFURA_KEY,https://rpc.ankr.com/eth

# Recommended (for reliable CAPTCHA solving)
TWOCAPTCHA_API_KEY=your_2captcha_key
CAPSOLVER_API_KEY=your_capsolver_key

# Optional (for privacy)
PROXIES=http://user:pass@host:port

# Bot settings
HEADLESS=false  # Set to true for cloud deployment
```

### Step 4: Deploy Locally

**Windows:**
```bash
deploy_local.bat
```

**Linux/Mac:**
```bash
chmod +x deploy_local.sh
./deploy_local.sh
```

Or manually:
```bash
docker-compose build
docker-compose up -d
```

### Step 5: Monitor the Bots

View logs:
```bash
docker-compose logs -f
```

Check status:
```bash
docker-compose ps
```

Stop the bots:
```bash
docker-compose down
```

## Architecture

### Wallet Structure

The wallet system uses a hierarchical deterministic (HD) wallet approach:

- **Master Mnemonic**: A single BIP-39 mnemonic that derives all wallets
- **Coinbot Wallets**: Multiple wallets for faucet collection
- **Airfarm Wallets**: Multiple wallets for airdrop farming
- **Master Wallet**: Receives sweeps from coinbot wallets
- **Middleware Wallet** (optional): Additional privacy layer

### Consolidation Flow

1. Coinbot wallets collect funds from faucets
2. When balance exceeds threshold, funds are swept to master wallet
3. Master wallet funds airfarm wallets when they need gas
4. Airfarm wallets spend funds on airdrop interactions

### Encrypted Storage

All wallet data is encrypted using:
- PBKDF2HMAC with SHA-256 for key derivation
- Fernet (AES-128) for encryption
- Password-based encryption (WALLET_STORE_KEY)

## Configuration Reference

### Wallet Settings

| Variable | Description | Required |
|----------|-------------|----------|
| WALLET_STORE_PATH | Path to encrypted wallet store | Yes |
| WALLET_STORE_KEY | Password to decrypt wallet store | Yes |

### RPC Settings

| Variable | Description | Required |
|----------|-------------|----------|
| WEB3_RPC_URLS | Comma-separated list of RPC endpoints | Yes |

### CAPTCHA Settings

| Variable | Description | Required |
|----------|-------------|----------|
| TWOCAPTCHA_API_KEY | 2Captcha API key | No |
| CAPSOLVER_API_KEY | Capsolver API key | No |
| OCR_SPACE_API_KEY | OCR.space API key | No |

### Consolidation Settings

| Variable | Description | Default |
|----------|-------------|---------|
| CONSOLIDATION_ENABLED | Enable consolidation | true |
| CONSOLIDATION_MIN_BALANCE_ETH | Minimum balance to trigger sweep | 0.02 |
| CONSOLIDATION_GAS_BUFFER_ETH | Gas buffer to leave in wallet | 0.005 |
| CONSOLIDATION_DELAY_MIN_SECONDS | Minimum delay between sweeps | 10 |
| CONSOLIDATION_DELAY_MAX_SECONDS | Maximum delay between sweeps | 30 |

### Airfarm Funding Settings

| Variable | Description | Default |
|----------|-------------|---------|
| AIRFARM_FUNDING_ENABLED | Enable auto-funding of airfarm wallets | true |
| AIRFARM_MIN_FUND_BALANCE_ETH | Minimum balance before funding | 0.03 |
| AIRFARM_FUND_AMOUNT_ETH | Amount to fund airfarm wallets | 0.06 |

## Cloud Deployment (Oracle Cloud)

### Prerequisites

- Oracle Cloud account with free tier
- OCI API key configured
- Terraform installed

### Steps

1. Configure Terraform variables in `terraform/terraform.tfvars`:
```hcl
tenancy_ocid = "your_tenancy_ocid"
user_ocid = "your_user_ocid"
fingerprint = "your_api_key_fingerprint"
private_key_path = "path/to/private_key"
ssh_public_key_path = "path/to/ssh_public_key"
compartment_ocid = "your_compartment_ocid"
region = "us-ashburn-1"
```

2. Initialize Terraform:
```bash
cd terraform
terraform init
```

3. Apply the configuration:
```bash
terraform apply
```

4. Note the public IP address from the output.

### GitHub Actions CI/CD

The repository includes a GitHub Actions workflow for automated deployment:

1. Add the following secrets to your GitHub repository:
   - `DOCKER_USERNAME`
   - `DOCKER_PASSWORD`
   - `SERVER_IP` (Oracle Cloud VM IP)
   - `SSH_PRIVATE_KEY`
   - `BOT_ENV` (your .env file content)

2. Push to the main branch to trigger deployment.

## Troubleshooting

### Docker Issues

If Docker fails to start:
```bash
# Check Docker status
docker --version
docker-compose --version

# Restart Docker
# Windows: Restart Docker Desktop
# Linux: sudo systemctl restart docker
```

### Wallet Decryption Issues

If you get wallet decryption errors:
- Ensure WALLET_STORE_KEY matches what you set during wallet generation
- Verify data/wallets.enc exists and is not corrupted
- Try regenerating wallets if the file is corrupted

### RPC Connection Issues

If you get RPC connection errors:
- Verify your WEB3_RPC_URLS are correct
- Try using public RPC endpoints like https://rpc.ankr.com/eth
- Check your internet connection

### Browser Issues

If the bot fails with browser errors:
- Ensure Chrome is installed
- Set HEADLESS=false to see the browser
- Check Chrome driver compatibility

## Security Best Practices

1. **Never share your mnemonic** - Store it offline securely
2. **Never commit .env or data/wallets.enc** to version control
3. **Use strong WALLET_STORE_KEY** - At least 12 characters
4. **Enable consolidation** - Regularly sweep funds to master wallet
5. **Use proxies** - For additional privacy when farming
6. **Monitor logs** - Regularly check for suspicious activity

## Support

For issues or questions:
1. Check the logs: `docker-compose logs -f`
2. Review this documentation
3. Check the main README.md file

## License

This project is provided for educational purposes only. Use responsibly and in compliance with applicable laws and terms of service of the platforms you interact with.

#!/usr/bin/env python3
"""
Wallet generation script with BIP-39 mnemonic support.
Generates wallets from a master mnemonic and creates encrypted wallet store.
"""

import os
import json
import secrets
import getpass
from pathlib import Path
from mnemonic import Mnemonic
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64


def print_header(text):
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def derive_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
        backend=default_backend(),
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode()))


def encrypt_wallet_store(wallet_data: dict, password: str, output_path: Path) -> None:
    payload = json.dumps(wallet_data, indent=2).encode('utf-8')
    salt = os.urandom(16)
    key = derive_key(password, salt)
    token = Fernet(key).encrypt(payload)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('wb') as f:
        f.write(salt + token)

    print(f"✓ Encrypted wallet store written to {output_path}")


def derive_wallet(index: int, mnemonic: str):
    """Derive wallet at a given index from the master mnemonic."""
    seed = Bip39SeedGenerator(mnemonic).Generate()
    bip44_mst = Bip44.FromSeed(seed, Bip44Coins.ETHEREUM)
    bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
    bip44_addr = bip44_acc.AddressIndex(index)
    return {
        'address': bip44_addr.PublicKey().ToAddress(),
        'private_key': bip44_addr.PrivateKey().Raw().ToHex()
    }


def generate_wallet_data():
    """Generate wallet data structure for both coinbot and airfarm."""
    print_header("Wallet Generation Configuration")
    
    # Get mnemonic
    use_existing = input("Do you have an existing BIP-39 mnemonic? (y/N): ").strip().lower()
    if use_existing == 'y':
        mnemonic = input("Enter your BIP-39 mnemonic (12 or 24 words, space-separated): ").strip()
        # Validate mnemonic
        mnemo = Mnemonic("english")
        if not mnemo.check(mnemonic):
            print("❌ Invalid mnemonic. Please check and try again.")
            return None
    else:
        words = input("How many words in mnemonic? (12 or 24, default 12): ").strip()
        word_count = 12 if not words or words == '12' else 24
        mnemonic = Bip39MnemonicGenerator().FromWordsNumber(word_count)
        print(f"\n⚠️  IMPORTANT: Save this mnemonic securely!")
        print(f"Your mnemonic: {mnemonic}")
        print("Store it offline. Never share it!")
        confirm = input("\nHave you saved your mnemonic? (type 'yes' to continue): ")
        if confirm.lower() != 'yes':
            print("Aborted. Please save your mnemonic and run again.")
            return None

    # Get number of wallets for each bot
    num_coinbot = int(input("Number of coinbot (faucet) wallets (default 5): ").strip() or "5")
    num_airfarm = int(input("Number of airfarm wallets (default 3): ").strip() or "3")

    # Generate coinbot wallets (faucet collectors)
    print(f"\nGenerating {num_coinbot} coinbot wallets...")
    coinbot_wallets = []
    for i in range(num_coinbot):
        wallet = derive_wallet(i, mnemonic)
        wallet['role'] = 'coinbot_farm'
        coinbot_wallets.append(wallet)
        print(f"  Coinbot wallet {i+1}: {wallet['address']}")

    # Generate airfarm wallets (airdrop farmers)
    print(f"\nGenerating {num_airfarm} airfarm wallets...")
    airfarm_wallets = []
    for i in range(num_coinbot, num_coinbot + num_airfarm):
        wallet = derive_wallet(i, mnemonic)
        wallet['role'] = 'airfarm_farm'
        airfarm_wallets.append(wallet)
        print(f"  Airfarm wallet {i-num_coinbot+1}: {wallet['address']}")

    # Generate master wallet (receives coinbot sweeps)
    master_index = num_coinbot + num_airfarm
    master_wallet = derive_wallet(master_index, mnemonic)
    master_wallet['role'] = 'master'
    print(f"\nMaster wallet (receives sweeps): {master_wallet['address']}")

    # Optional: middleware wallet (breaks on-chain link)
    use_middleware = input("\nAdd middleware wallet for extra privacy? (y/N): ").strip().lower()
    middleware_wallet = None
    if use_middleware == 'y':
        middleware_index = master_index + 1
        middleware_wallet = derive_wallet(middleware_index, mnemonic)
        middleware_wallet['role'] = 'middleware'
        print(f"Middleware wallet: {middleware_wallet['address']}")

    # Build wallet data structure
    wallets = coinbot_wallets + airfarm_wallets + [master_wallet]
    if middleware_wallet:
        wallets.append(middleware_wallet)

    wallet_data = {
        'mnemonic': mnemonic,
        'wallets': wallets
    }

    return wallet_data


def main():
    print_header("Autonomous Airdrop Bot - Wallet Generator")
    
    # Generate wallet data
    wallet_data = generate_wallet_data()
    if not wallet_data:
        return

    # Get encryption password
    print_header("Encryption Setup")
    print("You need to set a password to encrypt your wallet store.")
    print("This password will be required in your .env file as WALLET_STORE_KEY")
    password = getpass.getpass("Enter encryption password: ")
    confirm = getpass.getpass("Confirm password: ")
    
    if password != confirm:
        print("❌ Passwords do not match. Aborted.")
        return
    
    if len(password) < 8:
        print("❌ Password must be at least 8 characters. Aborted.")
        return

    # Encrypt and save
    output_path = Path('data/wallets.enc')
    encrypt_wallet_store(wallet_data, password, output_path)

    # Save unencrypted backup (optional, warn user)
    save_backup = input("\nSave unencrypted backup JSON? (NOT recommended for production) (y/N): ").strip().lower()
    if save_backup == 'y':
        backup_path = Path('data/wallets_backup.json')
        with backup_path.open('w') as f:
            json.dump(wallet_data, f, indent=2)
        print(f"⚠️  Unencrypted backup saved to {backup_path} - DELETE THIS AFTER BACKUP!")

    # Update .env file
    print_header("Environment Configuration")
    env_path = Path('.env')
    if env_path.exists():
        add_to_env = input(f"Update {env_path} with WALLET_STORE_KEY? (y/N): ").strip().lower()
        if add_to_env == 'y':
            with env_path.open('a') as f:
                f.write(f"\n# Wallet store encryption key\nWALLET_STORE_KEY={password}\n")
            print(f"✓ Updated {env_path} with WALLET_STORE_KEY")

    print_header("Setup Complete")
    print(f"""
Next steps:
1. Your encrypted wallet store is at: {output_path}
2. Add WALLET_STORE_KEY={password} to your .env file
3. The wallet store contains:
   - {len([w for w in wallet_data['wallets'] if 'coinbot' in w['role']])} coinbot wallets (faucet collectors)
   - {len([w for w in wallet_data['wallets'] if 'airfarm' in w['role']])} airfarm wallets (airdrop farmers)
   - 1 master wallet (receives coinbot sweeps)
   - 1 middleware wallet (if enabled)
4. Run 'python setup_bot.py' if you haven't already to set up the environment
5. Start the bots with docker-compose up -d

⚠️  SECURITY REMINDERS:
- Never share your mnemonic or wallet store
- Never commit .env or data/wallets.enc to version control
- Keep backups of your mnemonic offline
- Your WALLET_STORE_KEY is required to decrypt the wallet store
""")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Quick setup script - generates minimal wallet store for testing
"""
import os
import json
import secrets
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
import base64
from eth_account import Account

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

    print(f"[OK] Encrypted wallet store written to {output_path}")

def main():
    # Generate a simple test wallet
    account = Account.create()
    
    wallet_data = {
        'mnemonic': 'test mnemonic replace with real one',
        'wallets': [
            {
                'address': account.address,
                'private_key': account.key.hex(),
                'role': 'coinbot_farm'
            },
            {
                'address': account.address,
                'private_key': account.key.hex(),
                'role': 'airfarm_farm'
            },
            {
                'address': account.address,
                'private_key': account.key.hex(),
                'role': 'master'
            }
        ]
    }

    password = "testpassword123"
    output_path = Path('data/wallets.enc')
    encrypt_wallet_store(wallet_data, password, output_path)
    
    print(f"\n[WARNING] TEST WALLET STORE CREATED")
    print(f"   WALLET_STORE_KEY: {password}")
    print(f"   [WARNING] This is for testing only! Replace with real wallets using generate_wallets.py")
    print(f"\nAdd this to your .env file:")
    print(f"WALLET_STORE_KEY={password}")

if __name__ == "__main__":
    main()

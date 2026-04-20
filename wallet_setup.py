import argparse
import base64
import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


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

    print(f"Encrypted wallet store written to {output_path}")


def load_wallet_json(path: Path) -> dict:
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description='Generate encrypted wallet store for the bot.')
    parser.add_argument('--input', '-i', required=True, help='Input JSON file containing wallet data')
    parser.add_argument('--output', '-o', default='data/wallets.enc', help='Encrypted wallet output path')
    parser.add_argument('--key', '-k', required=True, help='Encryption key / password for wallet store')
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f'Input file not found: {input_path}')

    wallet_data = load_wallet_json(input_path)
    if 'wallets' not in wallet_data:
        raise ValueError('Input JSON must contain a top-level "wallets" array')

    encrypt_wallet_store(wallet_data, args.key, output_path)


if __name__ == '__main__':
    main()

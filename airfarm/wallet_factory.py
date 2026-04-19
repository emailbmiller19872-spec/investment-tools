import os
import json
import logging
import secrets
import argparse
import base64
import getpass
from datetime import datetime
from eth_account import Account
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

Account.enable_unaudited_hdwallet_features()

DEFAULT_WALLET_DIR = 'data'
DEFAULT_WALLET_FILE = 'data/wallets.json'
DEFAULT_ENCRYPTED_WALLET_FILE = 'data/wallets.enc'


def _derive_fernet_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=390000,
    )
    return base64.urlsafe_b64encode(kdf.derive(password.encode('utf-8')))


def encrypt_payload(payload: dict, password: str) -> str:
    salt = secrets.token_bytes(16)
    key = _derive_fernet_key(password, salt)
    token = Fernet(key).encrypt(json.dumps(payload).encode('utf-8'))
    return json.dumps({
        'salt': base64.b64encode(salt).decode('utf-8'),
        'ciphertext': token.decode('utf-8')
    })


def decrypt_payload(encrypted_text: str, password: str) -> dict:
    data = json.loads(encrypted_text)
    salt = base64.b64decode(data['salt'])
    ciphertext = data['ciphertext'].encode('utf-8')
    key = _derive_fernet_key(password, salt)
    plain = Fernet(key).decrypt(ciphertext)
    return json.loads(plain.decode('utf-8'))


def generate_mnemonic(words=12) -> str:
    if words not in (12, 15, 18, 21, 24):
        raise ValueError('Mnemonic word count must be one of 12, 15, 18, 21, or 24.')
    return Bip39MnemonicGenerator().FromWordsNumber(words)


def derive_wallets_from_mnemonic(mnemonic: str, count=3, start_index=0) -> list[dict]:
    seed = Bip39SeedGenerator(mnemonic).Generate()
    bip44_mst = Bip44.FromSeed(seed, Bip44Coins.ETHEREUM)
    bip44_acc = bip44_mst.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT)
    wallets = []
    for index in range(start_index, start_index + count):
        child = bip44_acc.AddressIndex(index)
        wallets.append({
            'address': child.PublicKey().ToAddress(),
            'private_key': child.PrivateKey().Raw().ToHex(),
            'derivation_path': f"m/44'/60'/0'/0/{index}",
            'label': f'wallet-{index + 1}',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'notes': 'derived from mnemonic'
        })
    return wallets


def save_encrypted_wallets(wallets: list[dict], password: str, path: str = DEFAULT_ENCRYPTED_WALLET_FILE) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {'wallets': wallets}
    encrypted = encrypt_payload(payload, password)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(encrypted)


def load_encrypted_wallets(password: str, path: str = DEFAULT_ENCRYPTED_WALLET_FILE) -> list[dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f'Encrypted wallet store not found: {path}')
    with open(path, 'r', encoding='utf-8') as f:
        encrypted_text = f.read()
    payload = decrypt_payload(encrypted_text, password)
    wallets = payload.get('wallets', [])
    if not isinstance(wallets, list):
        raise ValueError('Encrypted wallet store did not contain a wallet list.')
    return wallets


class WalletStore:
    def __init__(self, path=DEFAULT_WALLET_FILE):
        self.path = os.getenv('WALLET_FILE', path)
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self.wallets = self.load_wallets()

    def load_wallets(self):
        if not os.path.exists(self.path):
            return []
        try:
            with open(self.path, 'r', encoding='utf-8') as wallet_file:
                return json.load(wallet_file)
        except Exception as e:
            self.logger.error(f'Failed to load wallet store: {e}')
            return []

    def save_wallets(self, wallets):
        self.wallets = wallets
        try:
            with open(self.path, 'w', encoding='utf-8') as wallet_file:
                json.dump(self.wallets, wallet_file, indent=2)
            self.logger.info(f'Saved {len(wallets)} wallets to {self.path}')
        except Exception as e:
            self.logger.error(f'Failed to save wallet store: {e}')

    def save_encrypted_wallets(self, wallets, password, path=None):
        path = path or os.getenv('WALLET_STORE_FILE', DEFAULT_ENCRYPTED_WALLET_FILE)
        save_encrypted_wallets(wallets, password, path)
        self.logger.info(f'Saved encrypted wallet store to {path}')

    def load_encrypted_wallets(self, password, path=None):
        path = path or os.getenv('WALLET_STORE_FILE', DEFAULT_ENCRYPTED_WALLET_FILE)
        try:
            return load_encrypted_wallets(password, path)
        except Exception as e:
            self.logger.error(f'Failed to load encrypted wallet store: {e}')
            return []

    def create_wallet(self, label=None, funding_source=None, notes=None):
        private_key = secrets.token_hex(32)
        account = Account.from_key(private_key)
        wallet = {
            'address': account.address,
            'private_key': private_key,
            'label': label or f'wallet-{len(self.wallets) + 1}',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'funding_source': funding_source or os.getenv('FUNDING_SOURCE', 'manual'),
            'notes': notes or ''
        }
        self.wallets.append(wallet)
        self.save_wallets(self.wallets)
        return wallet

    def create_wallet_batch(self, count=3, funding_source=None):
        new_wallets = []
        for _ in range(count):
            new_wallets.append(self.create_wallet(funding_source=funding_source))
        return new_wallets

    def get_wallets(self):
        return self.wallets

    def get_wallet_by_index(self, index=0):
        return self.wallets[index] if index < len(self.wallets) else None

    def filter_high_quality_wallets(self):
        return [w for w in self.wallets if w.get('funding_source') and w.get('created_at')]

    def get_wallet_profiles(self):
        return [{
            'address': w['address'],
            'label': w.get('label'),
            'funding_source': w.get('funding_source'),
            'created_at': w.get('created_at')
        } for w in self.wallets]


def _create_encrypted_wallet_store_cli():
    parser = argparse.ArgumentParser(description='Generate deterministic Ethereum wallets and encrypt the wallet store.')
    parser.add_argument('--mnemonic', help='Existing BIP-39 mnemonic to derive wallets from')
    parser.add_argument('--words', type=int, default=12, choices=[12, 15, 18, 21, 24], help='Mnemonic length in words')
    parser.add_argument('--count', type=int, default=5, help='Number of wallets to derive')
    parser.add_argument('--start-index', type=int, default=0, help='Starting derivation index')
    parser.add_argument('--output', default=DEFAULT_ENCRYPTED_WALLET_FILE, help='Encrypted wallet store path')
    parser.add_argument('--no-encrypt', action='store_true', help='Also write a plaintext wallet JSON file for debugging')
    args = parser.parse_args()

    mnemonic = args.mnemonic or generate_mnemonic(args.words)
    wallets = derive_wallets_from_mnemonic(mnemonic, count=args.count, start_index=args.start_index)

    password = os.getenv('WALLET_STORE_KEY')
    if not password:
        password = getpass.getpass('Enter encryption password for wallet store: ').strip()
    if not password:
        raise ValueError('Wallet store key is required to encrypt wallet data.')

    save_encrypted_wallets(wallets, password, args.output)
    print(f'Encrypted wallet store saved to {args.output}')
    print('Keep your wallet encryption key private. You can decrypt this file with the same key at runtime.')
    print(f'Mnemonic used: {mnemonic}')
    if args.no_encrypt:
        plaintext_path = os.path.splitext(args.output)[0] + '.json'
        with open(plaintext_path, 'w', encoding='utf-8') as pf:
            json.dump({'mnemonic': mnemonic, 'wallets': wallets}, pf, indent=2)
        print(f'Plaintext wallet file saved to {plaintext_path} (remove this after verification)')


if __name__ == '__main__':
    _create_encrypted_wallet_store_cli()

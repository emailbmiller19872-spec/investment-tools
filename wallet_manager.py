import os
import json
import base64
import logging
from decimal import Decimal
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account


class WalletManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.rpc_urls = self._load_env_list('WEB3_RPC_URLS') or [os.getenv('WEB3_RPC_URL', 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY')]
        self.w3 = self._get_working_provider()

        self.wallet_store_path = os.getenv('WALLET_STORE_PATH', 'data/wallets.enc')
        self.wallet_store_key = os.getenv('WALLET_STORE_KEY', '')
        self.wallets = self._load_wallet_store()

        self.default_wallet = self._find_wallet_by_role('default')
        self.farm_wallets = [wallet for wallet in self.wallets if wallet.get('role') == 'farm']
        self.master_wallet = self._find_wallet_by_role('master')
        self.middleware_wallet = self._find_wallet_by_role('middleware')

    def _derive_fernet_key(self, password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=390000,
            backend=default_backend()
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def _decrypt_wallet_store(self, path, password):
        try:
            with open(path, 'rb') as f:
                file_data = f.read()

            if len(file_data) < 16:
                raise ValueError('Encrypted wallet store is invalid or corrupted')

            salt = file_data[:16]
            token = file_data[16:]
            key = self._derive_fernet_key(password, salt)
            return Fernet(key).decrypt(token).decode('utf-8')
        except Exception as e:
            self.logger.error(f'Failed to decrypt wallet store: {e}')
            return None

    def _load_wallet_store(self):
        if not self.wallet_store_key:
            self.logger.error('WALLET_STORE_KEY is not configured. Encrypted wallet store cannot be loaded.')
            return []

        wallet_path = Path(self.wallet_store_path)
        if not wallet_path.exists():
            self.logger.error(f'Encrypted wallet store not found at {wallet_path}')
            return []

        decrypted = self._decrypt_wallet_store(wallet_path, self.wallet_store_key)
        if not decrypted:
            return []

        try:
            store = json.loads(decrypted)
            wallets = []
            for item in store.get('wallets', []):
                wallet = self._build_wallet(
                    item.get('address'),
                    item.get('private_key'),
                    item.get('role', 'farm')
                )
                if wallet:
                    wallets.append(wallet)
            if not wallets:
                self.logger.warning('Encrypted wallet store loaded but contains no valid wallets')
            return wallets
        except Exception as e:
            self.logger.error(f'Invalid wallet store format: {e}')
            return []

    def _get_working_provider(self):
        last_error = None
        for url in self.rpc_urls:
            try:
                provider = Web3.HTTPProvider(url)
                w3 = Web3(provider)
                if w3.is_connected():
                    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    self.logger.info(f'Connected to RPC provider: {url}')
                    return w3
                self.logger.warning(f'RPC endpoint not reachable: {url}')
            except Exception as e:
                last_error = e
                self.logger.warning(f'RPC connection failed for {url}: {e}')
        self.logger.error('No working RPC provider found. Check WEB3_RPC_URLS or WEB3_RPC_URL settings.')
        if self.rpc_urls:
            return Web3(Web3.HTTPProvider(self.rpc_urls[0]))
        return Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR_INFURA_KEY'))

    def _find_wallet_by_role(self, role):
        for wallet in self.wallets:
            if wallet.get('role') == role:
                return wallet
        return None

    def _to_checksum_address(self, address):
        try:
            return Web3.to_checksum_address(address)
        except Exception:
            return None

    def _build_wallet(self, address, private_key, role):
        if not address:
            return None

        checksum = self._to_checksum_address(address)
        if not checksum:
            self.logger.warning(f"Invalid wallet address configured for role '{role}': {address}")
            return None

        wallet = {
            'address': checksum,
            'private_key': private_key,
            'role': role
        }

        if private_key:
            try:
                wallet['account'] = Account.from_key(private_key)
            except Exception:
                self.logger.warning(f"Invalid private key configured for role '{role}'")
                wallet['private_key'] = None

        return wallet

    def get_default_wallet(self):
        return self.default_wallet

    def get_farm_wallets(self):
        if self.farm_wallets:
            return self.farm_wallets

        return [self.default_wallet] if self.default_wallet else []

    def get_master_wallet(self):
        return self.master_wallet

    def get_middleware_wallet(self):
        return self.middleware_wallet

    def get_airfarm_wallets(self):
        """Get wallets with role 'airfarm_farm' for airdrop farming."""
        return [wallet for wallet in self.wallets if wallet.get('role') == 'airfarm_farm']

    def get_coinbot_wallets(self):
        """Get wallets with role 'coinbot_farm' for faucet collection."""
        return [wallet for wallet in self.wallets if wallet.get('role') == 'coinbot_farm']

    def get_airfarm_master_wallet(self):
        """Get the master wallet for airfarm (receives sweeps from coinbot)."""
        return self.master_wallet

    def get_coinbot_master_wallet(self):
        """Get the master wallet for coinbot (same as airfarm master in this setup)."""
        return self.master_wallet

    def get_airfarm_middleware_wallet(self):
        """Get the middleware wallet for airfarm (optional privacy layer)."""
        return self.middleware_wallet

    def get_airfarm_final_wallet(self):
        """Get the final wallet for airfarm (optional final sweep destination)."""
        # For now, return None - this can be configured later
        return None

    def get_wallet_by_address(self, address):
        if not address:
            return None

        checksum = self._to_checksum_address(address)
        if not checksum:
            return None

        for wallet in self.wallets:
            if wallet.get('address') == checksum:
                return wallet

        return None

    def connect_wallet(self, driver, dapp_url):
        """Attempt to connect wallet to dApp (simplified)"""
        try:
            driver.get(dapp_url)
            self.logger.info(f"Attempting wallet connection to {dapp_url}")
            return True
        except Exception as e:
            self.logger.error(f"Wallet connection failed: {e}")
            return False

    def get_balance(self, token_address=None, wallet=None):
        wallet = wallet or self.default_wallet
        if not wallet or not wallet.get('address'):
            self.logger.warning('No wallet available for balance check')
            return Decimal(0)

        try:
            if token_address:
                contract = self.w3.eth.contract(address=self._to_checksum_address(token_address), abi=self._get_erc20_abi())
                balance = contract.functions.balanceOf(wallet['address']).call()
                decimals = contract.functions.decimals().call()
                return Decimal(balance) / Decimal(10 ** decimals)

            balance = self.w3.eth.get_balance(wallet['address'])
            return Decimal(self.w3.from_wei(balance, 'ether'))
        except Exception as e:
            self.logger.error(f"Error getting balance for {wallet['address']}: {e}")
            return Decimal(0)

    def update_balances(self):
        from database import Database
        db = Database()

        primary_balance = self.get_balance()
        db.update_balance('ETH', float(primary_balance))

        balances = db.get_balances()
        total_value = 0
        for token, amount, usd_value in balances:
            if usd_value:
                total_value += amount * usd_value

        self.logger.info(f"Total portfolio value: ${total_value:.2f}")

    def send_transaction(self, to_address, amount, wallet=None, token_address=None):
        wallet = wallet or self.default_wallet
        if not wallet or not wallet.get('address'):
            self.logger.error('No wallet available to sign transaction')
            return None

        if not wallet.get('private_key'):
            self.logger.error(f"Wallet {wallet['address']} is missing a private key")
            return None

        checksum_to = self._to_checksum_address(to_address)
        if not checksum_to:
            self.logger.error(f"Invalid destination address: {to_address}")
            return None

        try:
            if token_address:
                contract = self.w3.eth.contract(address=self._to_checksum_address(token_address), abi=self._get_erc20_abi())
                decimals = contract.functions.decimals().call()
                token_amount = int(Decimal(amount) * Decimal(10 ** decimals))
                tx = contract.functions.transfer(checksum_to, token_amount).build_transaction({
                    'from': wallet['address'],
                    'nonce': self.w3.eth.get_transaction_count(wallet['address']),
                    'gas': 200000,
                    'gasPrice': self.w3.eth.gas_price
                })
            else:
                tx = {
                    'to': checksum_to,
                    'value': int(Decimal(amount) * Decimal(10 ** 18)),
                    'gas': 21000,
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': self.w3.eth.get_transaction_count(wallet['address'])
                }

            signed_tx = self.w3.eth.account.sign_transaction(tx, wallet['private_key'])
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            self.logger.info(f"Transaction sent from {wallet['address']} to {checksum_to}: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            self.logger.error(f"Transaction failed from {wallet['address']} to {checksum_to}: {e}")
            return None

    def _get_erc20_abi(self):
        return [
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
            {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"}
        ]

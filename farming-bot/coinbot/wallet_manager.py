import os
import logging
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account

try:
    from web3_multi_provider import MultiProvider
except ImportError:
    MultiProvider = None

class WalletManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.addresses = [addr.strip() for addr in os.getenv('WALLET_ADDRESSES', '').split(',') if addr.strip()]
        self.address = os.getenv('WALLET_ADDRESS')
        self.private_key = os.getenv('PRIVATE_KEY')
        self.master_address = os.getenv('MASTER_WALLET_ADDRESS')
        self.master_private_key = os.getenv('MASTER_PRIVATE_KEY')

        if not self.address and self.addresses:
            self.address = self.addresses[0]

        self.farm_private_keys = [key.strip() for key in os.getenv('FARM_PRIVATE_KEYS', '').split(',') if key.strip()]
        if not self.farm_private_keys and self.private_key:
            self.farm_private_keys = [self.private_key]

        self.farm_wallets = []
        for index, wallet_address in enumerate(self.addresses):
            private_key = None
            if index < len(self.farm_private_keys):
                private_key = self.farm_private_keys[index]
            elif len(self.farm_private_keys) == 1:
                private_key = self.farm_private_keys[0]

            self.farm_wallets.append({
                'address': wallet_address,
                'private_key': private_key
            })

        for wallet in self.farm_wallets:
            if wallet['private_key'] is None:
                self.logger.warning(f"No private key configured for farm wallet {wallet['address']}")

        rpc_urls = [
            url.strip()
            for url in os.getenv('ETH_PROVIDER_URLS', os.getenv('ETH_PROVIDER_URL', 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY')).split(',')
            if url.strip()
        ]

        self.provider = self._create_provider(rpc_urls)
        self.w3 = Web3(self.provider)
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.account = None

        if self.private_key:
            try:
                self.account = Account.from_key(self.private_key)
            except Exception as e:
                self.logger.warning(f"Invalid private key provided: {e}")

    def get_wallet_addresses(self):
        if self.addresses:
            return self.addresses
        if self.address:
            return [self.address]
        return []

    def get_farm_wallets(self):
        return self.farm_wallets

    def get_farm_wallet_by_address(self, address):
        if not address:
            return None
        normalized = address.strip().lower()
        for wallet in self.farm_wallets:
            if wallet.get('address', '').strip().lower() == normalized:
                return wallet
        return None

    def get_wallet_by_address(self, address):
        if not address:
            return None
        normalized = address.strip().lower()
        for wallet in self.farm_wallets:
            if wallet.get('address', '').strip().lower() == normalized:
                return wallet
        if self.master_address and self.master_address.strip().lower() == normalized:
            return {'address': self.master_address, 'private_key': self.master_private_key}
        return None

    def connect_wallet(self, driver, dapp_url):
        """Attempt to connect wallet to dApp (simplified)."""
        try:
            driver.get(dapp_url)
            self.logger.info(f"Attempting wallet connection to {dapp_url}")
            return True
        except Exception as e:
            self.logger.error(f"Wallet connection failed: {e}")
            return False

    def _create_provider(self, urls):
        providers = [Web3.HTTPProvider(url, request_kwargs={"timeout": 10}) for url in urls]
        if MultiProvider and providers:
            try:
                return MultiProvider(providers)
            except Exception as e:
                self.logger.warning(f"MultiProvider failed, falling back to first provider: {e}")
        return providers[0] if providers else Web3.HTTPProvider('https://mainnet.infura.io/v3/YOUR_INFURA_KEY', request_kwargs={"timeout": 10})

    def get_balance(self, token_address=None, wallet=None):
        """Get wallet balance."""
        try:
            target_address = self.address
            if wallet and wallet.get('address'):
                target_address = wallet['address']

            if not target_address:
                self.logger.warning("No wallet address configured for balance check")
                return 0

            if token_address:
                contract = self.w3.eth.contract(address=token_address, abi=self._get_erc20_abi())
                balance = contract.functions.balanceOf(target_address).call()
                decimals = contract.functions.decimals().call()
                return balance / (10 ** decimals)

            balance = self.w3.eth.get_balance(target_address)
            return self.w3.from_wei(balance, 'ether')
        except Exception as e:
            self.logger.error(f"Error getting balance: {e}")
            return 0

    def update_balances(self):
        from .database import Database

        db = Database()
        addresses = self.get_wallet_addresses()

        for addr in addresses:
            if addr.lower() == self.address.lower():
                eth_balance = self.get_balance()
            else:
                eth_balance = self.get_balance(wallet={'address': addr})
            db.update_balance('ETH', eth_balance)

        balances = db.get_balances()
        total_value = 0
        for token, amount, usd_value in balances:
            if usd_value:
                total_value += amount * usd_value

        self.logger.info(f"Total portfolio value: ${total_value:.2f}")

    def send_transaction(self, to_address, amount, token_address=None, wallet=None):
        try:
            if wallet and wallet.get('private_key'):
                from_address = wallet.get('address')
                private_key = wallet.get('private_key')
            else:
                from_address = self.address
                private_key = self.private_key

            if not from_address or not private_key:
                self.logger.error("Private key and from address are required to send a transaction")
                return None

            if token_address:
                contract = self.w3.eth.contract(address=token_address, abi=self._get_erc20_abi())
                tx = contract.functions.transfer(to_address, amount).build_transaction({
                    'from': from_address,
                    'nonce': self.w3.eth.get_transaction_count(from_address),
                    'gas': 200000,
                    'gasPrice': self.w3.eth.gas_price
                })
            else:
                tx = {
                    'to': to_address,
                    'value': self.w3.to_wei(amount, 'ether'),
                    'gas': 21000,
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': self.w3.eth.get_transaction_count(from_address)
                }

            signed_tx = self.w3.eth.account.sign_transaction(tx, private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            self.logger.info(f"Transaction sent from {from_address} to {to_address}: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            self.logger.error(f"Transaction failed: {e}")
            return None

    def _get_erc20_abi(self):
        return [
            {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
            {"constant": False, "inputs": [{"name": "_to", "type": "address"}, {"name": "_value", "type": "uint256"}], "name": "transfer", "outputs": [{"name": "", "type": "bool"}], "type": "function"}
        ]

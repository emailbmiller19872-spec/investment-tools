import os
import json
import logging
import random
import threading
from web3 import Web3
from web3.middleware import geth_poa_middleware
from wallet_factory import load_encrypted_wallets

class WalletManager:
    def __init__(self):
        self.rpc_timeout = int(os.getenv('RPC_TIMEOUT_SECONDS', '10'))
        self.rpc_endpoints = self._load_rpc_endpoints()
        self.current_rpc = None
        self.w3 = None
        self.rpc_lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self._init_web3_provider()

        self.wallet_file = os.getenv('WALLET_FILE', 'data/wallets.json')
        wallet_dir = os.path.dirname(self.wallet_file)
        if wallet_dir:
            os.makedirs(wallet_dir, exist_ok=True)

        self.wallets = self._load_wallets()
        self.current_index = -1
        self.randomize_rotation = os.getenv('RANDOMIZE_WALLET_ROTATION', 'true').lower() in ('1', 'true', 'yes')
        self.consolidation_enabled = os.getenv('CONSOLIDATION_ENABLED', 'false').lower() in ('1', 'true', 'yes')
        self.master_wallet_address = os.getenv('MASTER_WALLET_ADDRESS')
        self.middleware_wallet = self._load_middleware_wallet()
        self.min_consolidation_balance = float(os.getenv('MIN_CONSOLIDATION_BALANCE_ETH', '0.02'))
        self.gas_buffer_eth = float(os.getenv('CONSOLIDATION_GAS_BUFFER_ETH', '0.005'))

    def _load_rpc_endpoints(self):
        raw_endpoints = os.getenv('RPC_ENDPOINTS', '')
        endpoints = [endpoint.strip() for endpoint in raw_endpoints.split(',') if endpoint.strip()]
        if endpoints:
            return endpoints

        infura_key = os.getenv('INFURA_KEY')
        if infura_key:
            return [f'https://mainnet.infura.io/v3/{infura_key}']

        raise ValueError('No RPC endpoints configured. Set RPC_ENDPOINTS or INFURA_KEY.')

    def _init_web3_provider(self):
        self.current_rpc = self.current_rpc or self.rpc_endpoints[0]
        self.w3 = Web3(Web3.HTTPProvider(self.current_rpc, request_kwargs={'timeout': self.rpc_timeout}))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        if not self.w3.is_connected():
            self.logger.warning(f'Initial RPC endpoint {self.current_rpc} did not connect, switching.')
            self._switch_rpc(self.current_rpc)

    def _switch_rpc(self, failed_rpc=None):
        with self.rpc_lock:
            candidates = [rpc for rpc in self.rpc_endpoints if rpc != failed_rpc]
            if not candidates:
                candidates = self.rpc_endpoints
            self.current_rpc = random.choice(candidates)
            self.w3 = Web3(Web3.HTTPProvider(self.current_rpc, request_kwargs={'timeout': self.rpc_timeout}))
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            self.logger.info(f'Switched RPC endpoint to {self.current_rpc}')
            return self.current_rpc

    def _ensure_connection(self):
        if self.w3 is None or not self.w3.is_connected():
            self.logger.warning('Web3 connection lost, switching RPC endpoint')
            self._switch_rpc(self.current_rpc)

    def _load_wallets(self):
        wallets = []
        encrypted_path = os.getenv('WALLET_STORE_FILE', 'data/wallets.enc')
        wallet_store_key = os.getenv('WALLET_STORE_KEY')

        if wallet_store_key and os.path.exists(encrypted_path):
            try:
                wallets = load_encrypted_wallets(wallet_store_key, encrypted_path)
                self.logger.info(f'Loaded {len(wallets)} wallets from encrypted store')
            except Exception as e:
                self.logger.error(f'Failed to load encrypted wallet store: {e}')

        if not wallets and os.path.exists(self.wallet_file):
            try:
                with open(self.wallet_file, 'r', encoding='utf-8') as wallet_file:
                    data = json.load(wallet_file)
                if isinstance(data, list):
                    wallets = data
            except Exception as e:
                self.logger.error(f"Failed to load wallet store: {e}")

        if not wallets:
            address = os.getenv('WALLET_ADDRESS')
            private_key = os.getenv('PRIVATE_KEY')
            if address and private_key:
                wallets = [{'address': address, 'private_key': private_key, 'created_at': None, 'priority': 0}]

        if wallets:
            wallets = sorted(wallets, key=lambda w: w.get('priority', 100))
        return wallets

    def get_wallets(self):
        return self.wallets

    def get_wallet_by_address(self, address):
        """Return wallet dict matching the given address, or None."""
        if not address:
            return None
        address = address.lower()
        for wallet in self.wallets:
            if wallet.get('address', '').lower() == address:
                return wallet
        return None

    def get_active_wallet(self):
        if not self.wallets:
            return None
        with self.rpc_lock:
            if self.current_index < 0 or self.current_index >= len(self.wallets):
                self.current_index = 0
            return self.wallets[self.current_index]

    def rotate_wallet(self):
        if not self.wallets:
            return None
        with self.rpc_lock:
            if self.randomize_rotation:
                self.current_index = random.randrange(len(self.wallets))
            else:
                self.current_index = (self.current_index + 1) % len(self.wallets)
            wallet = self.wallets[self.current_index]
            self.logger.info(f"Selected wallet {wallet.get('address')} (index {self.current_index})")
            return wallet

    def connect_wallet(self, driver, wallet=None, dapp_url=None):
        wallet = wallet or self.get_active_wallet()
        if not wallet:
            self.logger.error('No wallet available to connect')
            return False

        self.logger.info(f"Simulating wallet connection for {wallet['address']} to {dapp_url}")
        return True

    def get_balance(self, wallet=None, token_address=None):
        try:
            self._ensure_connection()
            wallet = wallet or self.get_active_wallet()
            if not wallet:
                self.logger.warning('Balance query failed: no wallet available')
                return 0

            if token_address:
                contract = self.w3.eth.contract(address=token_address, abi=self._get_erc20_abi())
                balance = contract.functions.balanceOf(wallet['address']).call()
                decimals = contract.functions.decimals().call()
                return balance / (10 ** decimals)

            balance = self.w3.eth.get_balance(wallet['address'])
            return self.w3.from_wei(balance, 'ether')
        except Exception as e:
            self.logger.error(f"Error getting balance for {wallet.get('address') if wallet else 'unknown'}: {e}")
            self._switch_rpc(self.current_rpc)
            return 0

    def update_balances(self, token_address=None):
        from database import Database
        db = Database()
        wallet = self.get_active_wallet()
        if not wallet:
            self.logger.warning('Skipping balance update because no wallet is loaded')
            return

        eth_balance = self.get_balance(wallet=wallet, token_address=token_address)
        db.update_balance('ETH', eth_balance)
        self.logger.info(f"Updated ETH balance for {wallet['address']}: {eth_balance}")

    def _load_middleware_wallet(self):
        address = os.getenv('MIDDLEWARE_WALLET_ADDRESS')
        private_key = os.getenv('MIDDLEWARE_WALLET_PRIVATE_KEY')
        if address and private_key:
            return {'address': address, 'private_key': private_key}
        return None

    def get_master_address(self):
        return self.master_wallet_address

    def has_consolidation_config(self):
        if not self.consolidation_enabled:
            return False
        if not self.master_wallet_address:
            self.logger.warning('Consolidation is enabled but MASTER_WALLET_ADDRESS is not set')
            return False
        return True

    def is_master_wallet(self, wallet):
        return wallet and wallet.get('address', '').lower() == self.master_wallet_address.lower()

    def is_middleware_wallet(self, wallet):
        return wallet and self.middleware_wallet and wallet.get('address', '').lower() == self.middleware_wallet.get('address', '').lower()

    def get_consolidation_sources(self):
        sources = []
        for wallet in self.wallets:
            if self.is_master_wallet(wallet):
                continue
            if self.is_middleware_wallet(wallet):
                continue
            sources.append(wallet)
        return sources

    def calculate_native_sweep_amount(self, wallet):
        balance = self.get_balance(wallet=wallet)
        if balance <= self.min_consolidation_balance + self.gas_buffer_eth:
            return 0
        return round(balance - self.gas_buffer_eth, 8)

    def sweep_wallet_to_target(self, source_wallet, destination_address):
        amount = self.calculate_native_sweep_amount(source_wallet)
        if amount <= 0:
            self.logger.info(f"Skipping consolidation for {source_wallet['address']}: balance too low")
            return None

        self.logger.info(f"Sweeping {amount} ETH from {source_wallet['address']} to {destination_address}")
        return self.send_transaction(destination_address, amount, wallet=source_wallet)

    def sweep_farm_wallets_to_middleware(self):
        if not self.middleware_wallet:
            self.logger.warning('Middleware wallet not configured for consolidation flow')
            return []

        sweeps = []
        for wallet in self.get_consolidation_sources():
            tx_hash = self.sweep_wallet_to_target(wallet, self.middleware_wallet['address'])
            if tx_hash:
                sweeps.append({'from': wallet['address'], 'to': self.middleware_wallet['address'], 'hash': tx_hash})
        return sweeps

    def sweep_middleware_to_master(self):
        if not self.middleware_wallet or not self.master_wallet_address:
            self.logger.warning('Middleware or master wallet not configured for consolidation final leg')
            return None

        if self.middleware_wallet['address'].lower() == self.master_wallet_address.lower():
            self.logger.warning('Middleware wallet is the same as master wallet; skipping middleware sweep')
            return None

        return self.sweep_wallet_to_target(self.middleware_wallet, self.master_wallet_address)

    def sweep_all_farm_wallets_to_master(self):
        sweeps = []
        for wallet in self.get_consolidation_sources():
            tx_hash = self.sweep_wallet_to_target(wallet, self.master_wallet_address)
            if tx_hash:
                sweeps.append({'from': wallet['address'], 'to': self.master_wallet_address, 'hash': tx_hash})
        return sweeps

    def consolidate_all_wallets(self):
        if not self.has_consolidation_config():
            self.logger.info('Consolidation is disabled or not configured')
            return None

        if self.middleware_wallet:
            self.logger.info('Starting middleware consolidation flow')
            first_leg = self.sweep_farm_wallets_to_middleware()
            second_leg = self.sweep_middleware_to_master()
            return {'first_leg': first_leg, 'second_leg': second_leg}

        self.logger.info('Starting direct consolidation flow to master wallet')
        return {'direct_sweeps': self.sweep_all_farm_wallets_to_master()}

    def send_transaction(self, to_address, amount, wallet=None, token_address=None):
        wallet = wallet or self.get_active_wallet()
        if not wallet or 'private_key' not in wallet:
            self.logger.error('No wallet or private key available for transaction')
            return None

        try:
            self._ensure_connection()
            if token_address:
                contract = self.w3.eth.contract(address=token_address, abi=self._get_erc20_abi())
                tx = contract.functions.transfer(to_address, amount).build_transaction({
                    'from': wallet['address'],
                    'nonce': self.w3.eth.get_transaction_count(wallet['address']),
                    'gas': 200000,
                    'gasPrice': self.w3.eth.gas_price
                })
            else:
                tx = {
                    'to': to_address,
                    'value': self.w3.to_wei(amount, 'ether'),
                    'gas': 21000,
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': self.w3.eth.get_transaction_count(wallet['address'])
                }
            signed_tx = self.w3.eth.account.sign_transaction(tx, wallet['private_key'])
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            self.logger.info(f"Transaction sent from {wallet['address']}: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            self.logger.error(f"Transaction failed for {wallet['address']}: {e}")
            self._switch_rpc(self.current_rpc)
            return None

    def _get_erc20_abi(self):
        return [
            {'constant': True, 'inputs': [{'name': '_owner', 'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'name': 'balance', 'type': 'uint256'}], 'type': 'function'},
            {'constant': True, 'inputs': [], 'name': 'decimals', 'outputs': [{'name': '', 'type': 'uint8'}], 'type': 'function'},
            {'constant': False, 'inputs': [{'name': '_to', 'type': 'address'}, {'name': '_value', 'type': 'uint256'}], 'name': 'transfer', 'outputs': [{'name': '', 'type': 'bool'}], 'type': 'function'}
        ]

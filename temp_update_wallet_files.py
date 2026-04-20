from pathlib import Path

root = Path(r"c:\Users\charl\Desktop\autonomous-airdrop-capital-builder")

wallet_manager = root / "wallet_manager.py"
main_py = root / "main.py"
env_file = root / ".env"

wallet_manager.write_text(r"""import os
import logging
from decimal import Decimal
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account


class WalletManager:
    def __init__(self):
        self.rpc_url = os.getenv('WEB3_RPC_URL', 'https://mainnet.infura.io/v3/YOUR_INFURA_KEY')
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        self.logger = logging.getLogger(__name__)

        self.default_wallet = self._build_wallet(
            os.getenv('WALLET_ADDRESS'),
            os.getenv('PRIVATE_KEY'),
            'default'
        )

        self.airfarm_wallets = self._build_wallet_list(
            'AIRFARM_WALLET_ADDRESSES',
            'AIRFARM_WALLET_PRIVATE_KEYS',
            'airfarm'
        )

        self.coinbot_wallets = self._build_wallet_list(
            'COINBOT_FARM_WALLET_ADDRESSES',
            'COINBOT_FARM_PRIVATE_KEYS',
            'coinbot'
        )

        self.airfarm_master_wallet = self._build_wallet(
            os.getenv('AIRFARM_MASTER_WALLET_ADDRESS'),
            os.getenv('AIRFARM_MASTER_WALLET_PRIVATE_KEY'),
            'airfarm_master'
        )

        self.coinbot_master_wallet = self._build_wallet(
            os.getenv('COINBOT_MASTER_WALLET_ADDRESS'),
            os.getenv('COINBOT_MASTER_PRIVATE_KEY'),
            'coinbot_master'
        )

    def _to_checksum_address(self, address):
        try:
            return Web3.to_checksum_address(address)
        except Exception:
            return None

    def _load_env_list(self, key):
        return [item.strip() for item in os.getenv(key, '').split(',') if item.strip()]

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

    def _build_wallet_list(self, address_key, pk_key, role):
        addresses = self._load_env_list(address_key)
        private_keys = self._load_env_list(pk_key)
        wallets = []

        for index, address in enumerate(addresses):
            private_key = private_keys[index] if index < len(private_keys) else None
            wallet = self._build_wallet(address, private_key, role)
            if wallet:
                wallets.append(wallet)

        return wallets

    def get_default_wallet(self):
        return self.default_wallet

    def get_airfarm_wallets(self):
        return self.airfarm_wallets

    def get_coinbot_wallets(self):
        if self.coinbot_wallets:
            return self.coinbot_wallets
        return [self.default_wallet] if self.default_wallet else []

    def get_airfarm_master_wallet(self):
        return self.airfarm_master_wallet

    def get_coinbot_master_wallet(self):
        return self.coinbot_master_wallet

    def get_wallet_by_address(self, address):
        if not address:
            return None

        checksum = self._to_checksum_address(address)
        if not checksum:
            return None

        candidates = [
            self.default_wallet,
            self.airfarm_master_wallet,
            self.coinbot_master_wallet,
            *self.airfarm_wallets,
            *self.coinbot_wallets
        ]

        for wallet in candidates:
            if wallet and wallet.get('address') == checksum:
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
""", encoding="utf-8")

main_py.write_text(r"""import os
import time
import logging
from dotenv import load_dotenv
import schedule
from scraper import AirdropScraper
from task_automator import TaskAutomator
from wallet_manager import WalletManager
from proxy_manager import ProxyManager
from captcha_solver import CaptchaSolver
from database import Database
from consolidation import FundingEngine, ConsolidationEngine
from utils import setup_logging, random_delay

load_dotenv()
setup_logging()

class AutonomousAirdropBot:
    def __init__(self):
        self.scraper = AirdropScraper()
        self.automator = TaskAutomator()
        self.wallet = WalletManager()
        self.proxy_manager = ProxyManager()
        self.captcha_solver = CaptchaSolver()
        self.db = Database()
        self.funding_engine = FundingEngine(self.wallet)
        self.consolidation_engine = ConsolidationEngine(self.wallet)
        self.logger = logging.getLogger(__name__)

    def run_cycle(self):
        """Main cycle: discover, participate, track"""
        try:
            self.logger.info("Starting airdrop discovery cycle")
            airdrops = self.scraper.discover_airdrops()
            for airdrop in airdrops:
                if self.db.is_participated(airdrop['url']):
                    continue

                self.logger.info(f"Processing airdrop: {airdrop['title']}")
                success = self.automator.participate(airdrop)
                if success:
                    self.db.mark_participated(airdrop['url'])
                    self.logger.info(f"Successfully participated in {airdrop['title']}")
                else:
                    self.logger.warning(f"Failed to participate in {airdrop['title']}")
                random_delay(30, 60)

            self.wallet.update_balances()
            self.logger.info("Cycle completed")
        except Exception as e:
            self.logger.error(f"Error in run_cycle: {e}")
            time.sleep(300)

    def start(self):
        """Start the autonomous system"""
        self.logger.info("Starting Autonomous Airdrop Capital Builder")

        self.funding_engine.ensure_airfarm_funded()
        self.run_cycle()
        self.consolidation_engine.run_consolidation_cycle()

        interval_hours = int(os.getenv('CHECK_INTERVAL_HOURS', 6))
        schedule.every(interval_hours).hours.do(self._scheduled_cycle)

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            self.logger.info("Shutting down gracefully")

    def _scheduled_cycle(self):
        self.funding_engine.ensure_airfarm_funded()
        self.run_cycle()
        self.consolidation_engine.run_consolidation_cycle()

if __name__ == "__main__":
    bot = AutonomousAirdropBot()
    bot.start()
""", encoding="utf-8")

existing = env_file.read_text(encoding="utf-8")
new_lines = [
    "# Multi-wallet airfarm and coinbot funding/consolidation",
    "WEB3_RPC_URL=https://mainnet.infura.io/v3/YOUR_INFURA_KEY",
    "AIRFARM_WALLET_ADDRESSES=",
    "AIRFARM_WALLET_PRIVATE_KEYS=",
    "AIRFARM_MASTER_WALLET_ADDRESS=",
    "AIRFARM_MASTER_WALLET_PRIVATE_KEY=",
    "COINBOT_FARM_WALLET_ADDRESSES=",
    "COINBOT_FARM_PRIVATE_KEYS=",
    "COINBOT_MASTER_WALLET_ADDRESS=",
    "COINBOT_MASTER_PRIVATE_KEY=",
    "AIRFARM_FUNDING_ENABLED=true",
    "AIRFARM_MIN_FUND_BALANCE_ETH=0.03",
    "AIRFARM_FUND_AMOUNT_ETH=0.06",
    "AIRFARM_FUNDING_DELAY_MIN_SECONDS=15",
    "AIRFARM_FUNDING_DELAY_MAX_SECONDS=30",
    "CONSOLIDATION_ENABLED=true",
    "CONSOLIDATION_MIN_BALANCE_ETH=0.02",
    "CONSOLIDATION_GAS_BUFFER_ETH=0.002",
    "CONSOLIDATION_DELAY_MIN_SECONDS=8",
    "CONSOLIDATION_DELAY_MAX_SECONDS=20",
]
extra = "\n" + "\n".join(new_lines)
if "AIRFARM_WALLET_ADDRESSES" not in existing:
    env_file.write_text(existing.rstrip() + extra + "\n", encoding="utf-8")

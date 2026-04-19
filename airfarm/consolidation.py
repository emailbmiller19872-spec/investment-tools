import os
import random
import time
import logging
from utils import load_env_int, load_env_bool

class ConsolidationEngine:
    def __init__(self, wallet_manager):
        self.wallet_manager = wallet_manager
        self.master_address = os.getenv('MASTER_WALLET_ADDRESS')
        self.middleware_address = os.getenv('MIDDLEWARE_WALLET_ADDRESS')
        self.min_sweep_balance = float(os.getenv('MIN_SWEEP_BALANCE_NATIVE', '0.02'))
        self.reserve_amount = float(os.getenv('SWEEP_RESERVE_NATIVE', '0.003'))
        self.merchant_delay_seconds = int(os.getenv('MIDDLEWARE_TRANSFER_DELAY_SECONDS', '0'))
        self.logger = logging.getLogger(__name__)
        self.enabled = load_env_bool('CONSOLIDATION_ENABLED', True)

        if not self.master_address:
            self.logger.warning('MASTER_WALLET_ADDRESS is not configured; consolidation will not run.')
            self.enabled = False

    def get_farm_wallets(self):
        exclude = {addr.lower() for addr in [self.master_address, self.middleware_address] if addr}
        return [wallet for wallet in self.wallet_manager.get_wallets() if wallet.get('address', '').lower() not in exclude]

    def get_middleware_wallet(self):
        if not self.middleware_address:
            return None
        return self.wallet_manager.get_wallet_by_address(self.middleware_address)

    def get_master_wallet(self):
        return self.wallet_manager.get_wallet_by_address(self.master_address)

    def should_sweep(self, balance):
        return balance > (self.min_sweep_balance + self.reserve_amount)

    def sweep_wallet(self, wallet, destination):
        balance = self.wallet_manager.get_balance(wallet=wallet)
        self.logger.debug(f'Checking sweep wallet {wallet.get("address")}: balance {balance} ETH')
        if not self.should_sweep(balance):
            return False

        send_amount = max(0, balance - self.reserve_amount)
        if send_amount <= 0:
            self.logger.debug(f'Not enough available balance after reserve for {wallet.get("address")}')
            return False

        self.logger.info(f'Sweeping {send_amount:.6f} ETH from {wallet.get("address")} to {destination}')
        tx_hash = self.wallet_manager.send_transaction(destination, send_amount, wallet=wallet)
        if tx_hash:
            self.logger.info(f'Sweep transaction from {wallet.get("address")} succeeded: {tx_hash}')
            return True
        self.logger.warning(f'Sweep transaction from {wallet.get("address")} failed')
        return False

    def sweep_farm_wallets(self):
        farm_wallets = self.get_farm_wallets()
        if not farm_wallets:
            self.logger.warning('No farm wallets available for consolidation')
            return 0

        destination = self.middleware_address or self.master_address
        if not destination:
            self.logger.error('No consolidation destination configured')
            return 0

        sweeps = 0
        for wallet in farm_wallets:
            if self.sweep_wallet(wallet, destination):
                sweeps += 1
                time.sleep(random.uniform(10, 30))
        return sweeps

    def sweep_middleware_to_master(self):
        middleware_wallet = self.get_middleware_wallet()
        if not middleware_wallet:
            return 0

        if not self.master_address:
            self.logger.error('Master wallet not configured for middleware consolidation')
            return 0

        balance = self.wallet_manager.get_balance(wallet=middleware_wallet)
        if not self.should_sweep(balance):
            return 0

        if self.merchant_delay_seconds > 0:
            self.logger.info(f'Waiting {self.merchant_delay_seconds} seconds before middleware -> master sweep')
            time.sleep(self.merchant_delay_seconds)

        self.logger.info(f'Sweeping middleware wallet {middleware_wallet.get("address")} to master {self.master_address}')
        if self.sweep_wallet(middleware_wallet, self.master_address):
            return 1
        return 0

    def run_consolidation_cycle(self):
        if not self.enabled:
            self.logger.info('Consolidation is disabled')
            return

        self.logger.info('Starting consolidation cycle')
        sweeps = self.sweep_farm_wallets()
        if self.middleware_address:
            sweeps += self.sweep_middleware_to_master()
        self.logger.info(f'Consolidation cycle complete, total sweeps: {sweeps}')
        return sweeps
